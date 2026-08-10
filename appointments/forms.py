from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.country_codes import DEFAULT_COUNTRY_CODE
from accounts.models import UserProfile
from accounts.phone_fields import (
    clean_phone_local_number,
    phone_country_code_field,
    phone_local_number_field,
)
from accounts.phone_utils import combine_phone_number, split_phone_number
from configuracion.availability import validate_appointment_slot
from edificios.models import Building
from membresia.services import find_membership_for_booking, remaining_washes
from servicios.models import Service

from .models import Appointment, AppointmentStatus, PaymentType
from .recurrence import (
    MAX_RECURRENCE_OCCURRENCES,
    RECURRENCE_CHOICES,
    RECURRENCE_UNICA,
    generate_recurrence_dates,
)

VEHICLE_PROFILE_FIELDS = (
    'car_brand',
    'car_model',
    'car_color',
    'car_plate',
    'parking_level',
    'parking_number',
)


class AppointmentForm(forms.ModelForm):
    phone_country_code = phone_country_code_field()
    phone_local_number = phone_local_number_field()
    full_name = forms.CharField(
        label='Nombre completo',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Juan García'}),
    )
    recurrence = forms.ChoiceField(
        label='Cadencia',
        choices=RECURRENCE_CHOICES,
        initial=RECURRENCE_UNICA,
        required=False,
    )
    end_date = forms.DateField(
        label='Fecha fin',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    create_available_only = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, buildings=None, booking_ui=False, user=None, allow_recurrence=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking_user = user
        self.booking_ui = booking_ui
        self.allow_recurrence = allow_recurrence and not self.instance.pk
        self.unavailable_slots = []
        self.available_dates = []

        if buildings is None:
            buildings = Building.objects.none()

        self.fields['building'].queryset = buildings
        self.fields['building'].empty_label = 'Selecciona un edificio'
        self.fields['service'].queryset = Service.objects.filter(is_active=True)
        self.fields['service'].empty_label = 'Selecciona un servicio'

        wizard_mode = bool(booking_ui and self.allow_recurrence)

        if booking_ui:
            self.fields['date'].widget = forms.HiddenInput()
            self.fields['time'].widget = forms.HiddenInput()

        if wizard_mode:
            self.fields['first_name'].widget = forms.HiddenInput()
            self.fields['last_name'].widget = forms.HiddenInput()
            self.fields['first_name'].required = False
            self.fields['last_name'].required = False
            self.fields['full_name'].required = True
            for field_name in VEHICLE_PROFILE_FIELDS:
                self.fields[field_name].required = True
            self.fields['email'].label = 'Email'
            self.fields['email'].widget.attrs['placeholder'] = 'juan@email.com'
            self.fields['car_brand'].widget.attrs['placeholder'] = 'Toyota'
            self.fields['car_model'].widget.attrs['placeholder'] = 'Corolla 2022'
            self.fields['car_color'].widget.attrs['placeholder'] = 'Blanco'
            self.fields['car_plate'].widget.attrs['placeholder'] = 'ABC-123'
            self.fields['parking_level'].widget.attrs['placeholder'] = 'S1, S2, Nivel 1...'
            self.fields['parking_number'].widget.attrs['placeholder'] = 'A-12, 205...'
            self.fields['notes'].widget.attrs['placeholder'] = (
                'Manchas especiales, instrucciones de acceso...'
            )
            self.fields['notes'].widget.attrs['rows'] = 3
        else:
            self.fields.pop('full_name', None)
            # Keep vehicle fields off the staff edit booking UI so blank POST
            # values do not wipe appointment data.
            if booking_ui:
                for field_name in (*VEHICLE_PROFILE_FIELDS, 'notes'):
                    self.fields.pop(field_name, None)

        if not self.allow_recurrence:
            self.fields.pop('recurrence', None)
            self.fields.pop('end_date', None)
            self.fields.pop('create_available_only', None)
        else:
            self.fields['recurrence'].required = True
            self.fields['recurrence'].widget.attrs['id'] = 'id_recurrence'
            self.fields['end_date'].widget.attrs['id'] = 'id_end_date'

        if self.instance.pk and self.instance.phone_number:
            country_code, local_number = split_phone_number(self.instance.phone_number)
            self.initial.setdefault('phone_country_code', country_code)
            self.initial.setdefault('phone_local_number', local_number)
            if wizard_mode:
                full_name = f'{self.instance.first_name} {self.instance.last_name}'.strip()
                self.initial.setdefault('full_name', full_name)
        elif user is not None and not self.data:
            self._apply_user_defaults(user)

    def _apply_user_defaults(self, user):
        if user.first_name:
            self.initial.setdefault('first_name', user.first_name)
        if user.last_name:
            self.initial.setdefault('last_name', user.last_name)
        if user.email:
            self.initial.setdefault('email', user.email)

        full_name = f'{user.first_name} {user.last_name}'.strip()
        if full_name:
            self.initial.setdefault('full_name', full_name)

        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return

        self.initial.setdefault('phone_country_code', profile.phone_country_code)
        if profile.phone_number:
            self.initial.setdefault('phone_local_number', profile.phone_number)

        for field_name in VEHICLE_PROFILE_FIELDS:
            value = getattr(profile, field_name, '')
            if value:
                self.initial.setdefault(field_name, value)

    def clean_phone_local_number(self):
        country_code = self.cleaned_data.get('phone_country_code', DEFAULT_COUNTRY_CODE)
        return clean_phone_local_number(
            self.cleaned_data.get('phone_local_number', ''),
            country_code,
        )

    def clean_time(self):
        appointment_time = self.cleaned_data['time']
        if (
            appointment_time.minute not in (0, 30)
            or appointment_time.second
            or appointment_time.microsecond
        ):
            raise forms.ValidationError(
                'Selecciona una hora exacta o media hora, por ejemplo 10:00 o 10:30.'
            )
        return appointment_time

    def clean(self):
        cleaned_data = super().clean()
        building = cleaned_data.get('building')
        appointment_date = cleaned_data.get('date')
        appointment_time = cleaned_data.get('time')
        service = cleaned_data.get('service')
        recurrence = cleaned_data.get('recurrence') or RECURRENCE_UNICA
        end_date = cleaned_data.get('end_date')

        if self.booking_ui and self.allow_recurrence:
            full_name = (cleaned_data.get('full_name') or '').strip()
            if full_name:
                parts = full_name.split(None, 1)
                cleaned_data['first_name'] = parts[0][:100]
                cleaned_data['last_name'] = (parts[1] if len(parts) > 1 else parts[0])[:100]
            elif not cleaned_data.get('first_name') or not cleaned_data.get('last_name'):
                self.add_error('full_name', 'Indica tu nombre completo.')

        occurrence_dates = [appointment_date] if appointment_date else []

        if self.allow_recurrence and appointment_date:
            if recurrence != RECURRENCE_UNICA:
                if not end_date:
                    self.add_error(
                        'end_date',
                        'Indica la fecha fin para la frecuencia seleccionada.',
                    )
                elif end_date < appointment_date:
                    self.add_error(
                        'end_date',
                        'La fecha fin debe ser igual o posterior a la fecha de inicio.',
                    )
                else:
                    occurrence_dates = generate_recurrence_dates(
                        appointment_date,
                        end_date,
                        recurrence,
                    )
                    if len(occurrence_dates) > MAX_RECURRENCE_OCCURRENCES:
                        raise ValidationError(
                            f'Puedes crear máximo {MAX_RECURRENCE_OCCURRENCES} citas en una serie.'
                        )
                    if len(occurrence_dates) < 2:
                        self.add_error(
                            'end_date',
                            'Con la cadencia elegida no hay repeticiones entre esas fechas.',
                        )
            else:
                occurrence_dates = [appointment_date]

        cleaned_data['recurrence_dates'] = [d for d in occurrence_dates if d]
        create_available_only = bool(cleaned_data.get('create_available_only'))

        if building and appointment_time and cleaned_data['recurrence_dates']:
            exclude_id = self.instance.pk if self.instance.pk else None
            available = []
            unavailable = []
            for occurrence in cleaned_data['recurrence_dates']:
                error = validate_appointment_slot(
                    building,
                    occurrence,
                    appointment_time,
                    exclude_appointment_id=exclude_id,
                )
                if error:
                    unavailable.append(
                        {
                            'date': occurrence,
                            'label': occurrence.strftime('%d/%m/%Y'),
                            'reason': error,
                        }
                    )
                else:
                    available.append(occurrence)

            self.available_dates = available
            self.unavailable_slots = unavailable

            if unavailable:
                if create_available_only:
                    if not available:
                        raise ValidationError(
                            'Ninguna de las fechas de la serie está disponible.'
                        )
                    cleaned_data['recurrence_dates'] = available
                elif not available:
                    # Single booking: keep the concrete availability reason.
                    if len(unavailable) == 1:
                        raise ValidationError(unavailable[0]['reason'])
                    self.add_error(
                        None,
                        'Ninguna de las fechas de la serie está disponible.',
                    )
                else:
                    # Ask the user whether to create only the available ones.
                    self.add_error(
                        None,
                        'No se pueden crear todas las citas.',
                    )

        if service and self.booking_user and self.booking_user.is_authenticated:
            exclude_id = self.instance.pk if self.instance.pk else None
            subscription = find_membership_for_booking(
                self.booking_user,
                service,
                exclude_appointment_id=exclude_id,
            )
            cleaned_data['membership_subscription'] = subscription
            dates_count = len(cleaned_data.get('recurrence_dates') or [])
            # Only enforce membership when the form is otherwise ready to create.
            if (
                subscription
                and dates_count > 1
                and (create_available_only or not self.unavailable_slots)
            ):
                remaining = remaining_washes(
                    subscription,
                    service,
                    exclude_appointment_id=exclude_id,
                )
                if remaining is not None and remaining < dates_count:
                    raise ValidationError(
                        f'Tu membresía solo tiene {remaining} lavado(s) disponible(s) '
                        f'y esta serie crea {dates_count} citas.'
                    )
        else:
            cleaned_data['membership_subscription'] = None

        return cleaned_data

    def _apply_membership(self, appointment, subscription):
        if subscription:
            appointment.membership_subscription = subscription
            appointment.uses_membership = True
        elif not appointment.pk:
            appointment.membership_subscription = None
            appointment.uses_membership = False

    def _sync_user_profile(self, user):
        if not user or not user.is_authenticated:
            return

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save(update_fields=['first_name', 'last_name', 'email'])

        profile, _created = UserProfile.objects.get_or_create(user=user)
        profile.phone_country_code = self.cleaned_data['phone_country_code']
        profile.phone_number = self.cleaned_data['phone_local_number']
        for field_name in VEHICLE_PROFILE_FIELDS:
            setattr(profile, field_name, self.cleaned_data.get(field_name, ''))
        profile.save(
            update_fields=['phone_country_code', 'phone_number', *VEHICLE_PROFILE_FIELDS]
        )

    def save(self, commit=True):
        appointment = super().save(commit=False)
        appointment.phone_number = combine_phone_number(
            self.cleaned_data['phone_country_code'],
            self.cleaned_data['phone_local_number'],
        )
        self._apply_membership(
            appointment,
            self.cleaned_data.get('membership_subscription'),
        )
        if commit:
            appointment.save()
        return appointment

    def save_series(self, user):
        """Create one appointment per recurrence date. Returns the created list."""
        dates = self.cleaned_data.get('recurrence_dates') or [self.cleaned_data['date']]
        phone_number = combine_phone_number(
            self.cleaned_data['phone_country_code'],
            self.cleaned_data['phone_local_number'],
        )
        service = self.cleaned_data['service']
        created = []

        with transaction.atomic():
            self._sync_user_profile(user)
            for occurrence in dates:
                subscription = None
                if user and user.is_authenticated:
                    subscription = find_membership_for_booking(user, service)

                appointment = Appointment(
                    user=user,
                    building=self.cleaned_data['building'],
                    service=service,
                    first_name=self.cleaned_data['first_name'],
                    last_name=self.cleaned_data['last_name'],
                    phone_number=phone_number,
                    email=self.cleaned_data['email'],
                    car_brand=self.cleaned_data.get('car_brand', ''),
                    car_model=self.cleaned_data.get('car_model', ''),
                    car_color=self.cleaned_data.get('car_color', ''),
                    car_plate=self.cleaned_data.get('car_plate', ''),
                    parking_level=self.cleaned_data.get('parking_level', ''),
                    parking_number=self.cleaned_data.get('parking_number', ''),
                    notes=self.cleaned_data.get('notes', ''),
                    date=occurrence,
                    time=self.cleaned_data['time'],
                )
                self._apply_membership(appointment, subscription)
                appointment.save()
                created.append(appointment)

        return created

    class Meta:
        model = Appointment
        fields = [
            'building',
            'service',
            'first_name',
            'last_name',
            'email',
            'car_brand',
            'car_model',
            'car_color',
            'car_plate',
            'parking_level',
            'parking_number',
            'notes',
            'date',
            'time',
        ]
        labels = {
            'building': 'Edificio',
            'service': 'Servicio',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'car_brand': 'Marca del auto',
            'car_model': 'Modelo',
            'car_color': 'Color',
            'car_plate': 'Placa',
            'parking_level': 'Sótano',
            'parking_number': 'Número de parqueo',
            'notes': 'Notas adicionales',
            'date': 'Fecha',
            'time': 'Hora',
        }
        widgets = {
            'building': forms.Select(),
            'service': forms.Select(),
            'first_name': forms.TextInput(attrs={'placeholder': 'Nombre del cliente'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Apellido del cliente'}),
            'email': forms.EmailInput(attrs={'placeholder': 'cliente@correo.com'}),
            'car_brand': forms.TextInput(),
            'car_model': forms.TextInput(),
            'car_color': forms.TextInput(),
            'car_plate': forms.TextInput(),
            'parking_level': forms.TextInput(),
            'parking_number': forms.TextInput(),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'step': '1800'}),
        }


class AppointmentReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        label='Calificación',
        coerce=int,
        choices=[(i, str(i)) for i in range(1, 6)],
        widget=forms.RadioSelect,
        error_messages={'required': 'Elige una calificación del 1 al 5.'},
    )

    class Meta:
        model = Appointment
        fields = ['rating', 'review_comment']
        labels = {
            'review_comment': 'Comentario (opcional)',
        }
        widgets = {
            'review_comment': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Cuéntanos cómo estuvo el servicio...',
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            raise ValidationError('La cita no es válida.')
        if self.instance.status == AppointmentStatus.CANCELLED:
            raise ValidationError('No puedes calificar una cita cancelada.')
        if not self.instance.is_past:
            raise ValidationError(
                'Solo puedes calificar después de la fecha de la cita.'
            )
        if self.instance.is_reviewed:
            raise ValidationError('Esta cita ya fue calificada.')
        return cleaned_data

    def save(self, commit=True):
        appointment = super().save(commit=False)
        appointment.reviewed_at = timezone.now()
        if commit:
            appointment.save(update_fields=['rating', 'review_comment', 'reviewed_at'])
        return appointment


class AppointmentPaymentForm(forms.ModelForm):
    is_paid = forms.BooleanField(
        label='Marcar como pagada',
        required=False,
    )
    payment_type = forms.ChoiceField(
        label='Tipo de pago',
        choices=[
            ('', 'Selecciona un tipo'),
            (PaymentType.EFECTIVO, PaymentType.EFECTIVO.label),
            (PaymentType.TRANSFERENCIA, PaymentType.TRANSFERENCIA.label),
            (PaymentType.TARJETA, PaymentType.TARJETA.label),
        ],
        required=False,
    )

    class Meta:
        model = Appointment
        fields = ['is_paid', 'payment_type', 'payment_reference']
        labels = {
            'payment_reference': 'Referencia',
        }
        widgets = {
            'payment_reference': forms.TextInput(
                attrs={'placeholder': 'No. de boleta, voucher, últimos 4 dígitos...'}
            ),
        }

    def clean_payment_type(self):
        payment_type = self.cleaned_data.get('payment_type') or ''
        if payment_type == PaymentType.TARJETA:
            raise forms.ValidationError(
                'El pago con tarjeta estará disponible próximamente.'
            )
        return payment_type

    def clean(self):
        cleaned_data = super().clean()
        is_paid = cleaned_data.get('is_paid')
        payment_type = cleaned_data.get('payment_type') or ''
        if is_paid and not payment_type:
            self.add_error('payment_type', 'Indica el tipo de pago.')
        if not is_paid:
            cleaned_data['payment_type'] = ''
            cleaned_data['payment_reference'] = ''
        return cleaned_data

    def save(self, commit=True):
        appointment = super().save(commit=False)
        if appointment.is_paid:
            if not appointment.paid_at:
                appointment.paid_at = timezone.now()
        else:
            appointment.payment_type = ''
            appointment.payment_reference = ''
            appointment.paid_at = None
        if commit:
            appointment.save(
                update_fields=[
                    'is_paid',
                    'payment_type',
                    'payment_reference',
                    'paid_at',
                ]
            )
        return appointment


class AppointmentRescheduleForm(forms.ModelForm):
    def __init__(self, *args, booking_ui=False, **kwargs):
        super().__init__(*args, **kwargs)
        if booking_ui:
            self.fields['date'].widget = forms.HiddenInput()
            self.fields['time'].widget = forms.HiddenInput()

    def clean_time(self):
        appointment_time = self.cleaned_data['time']
        if (
            appointment_time.minute not in (0, 30)
            or appointment_time.second
            or appointment_time.microsecond
        ):
            raise forms.ValidationError(
                'Selecciona una hora exacta o media hora, por ejemplo 10:00 o 10:30.'
            )
        return appointment_time

    def clean(self):
        cleaned_data = super().clean()
        appointment_date = cleaned_data.get('date')
        appointment_time = cleaned_data.get('time')

        if self.instance and appointment_date and appointment_time:
            error = validate_appointment_slot(
                self.instance.building,
                appointment_date,
                appointment_time,
                exclude_appointment_id=self.instance.pk,
            )
            if error:
                raise ValidationError(error)

        return cleaned_data

    class Meta:
        model = Appointment
        fields = ['date', 'time']
        labels = {
            'date': 'Fecha',
            'time': 'Hora',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'step': '1800'}),
        }
