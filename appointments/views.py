from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET
import math

from configuracion.availability import (
    get_available_dates_in_month,
    get_available_time_slots,
)
from edificios.models import Building
from membresia.services import find_membership_for_booking, membership_credit_summary
from servicios.models import Service

from .forms import (
    AppointmentForm,
    AppointmentPaymentForm,
    AppointmentRescheduleForm,
    AppointmentReviewForm,
)
from .models import Appointment, AppointmentStatus


def home(request):
    services = Service.objects.filter(is_active=True).order_by('display_order', 'name')
    buildings_qs = Building.objects.filter(accepts_appointments=True).order_by('name')
    buildings = list(buildings_qs[:12])
    active_buildings_count = buildings_qs.count()

    washed_cars = Appointment.objects.filter(
        status=AppointmentStatus.ACTIVE,
        date__lte=timezone.localdate(),
    ).count()
    if washed_cars <= 0:
        washed_cars_display = '0'
    else:
        washed_cars_display = f'{math.ceil(washed_cars / 100) * 100}+'

    avg_rating = Appointment.objects.filter(rating__isnull=False).aggregate(
        avg=Avg('rating')
    )['avg']
    if avg_rating is None:
        average_rating_display = '—'
    else:
        average_rating_display = f'{avg_rating:.1f}★'

    return render(
        request,
        'home.html',
        {
            'services': services,
            'buildings': buildings,
            'washed_cars_display': washed_cars_display,
            'active_buildings_count': active_buildings_count,
            'average_rating_display': average_rating_display,
        },
    )


def _visible_buildings(user):
    if user.is_staff:
        return Building.objects.all()
    return Building.objects.filter(Q(created_by=user) | Q(admins=user)).distinct()


def _bookable_buildings(user):
    return Building.objects.filter(accepts_appointments=True)


def _visible_appointments(user):
    if user.is_staff:
        return Appointment.objects.all()
    visible_buildings = _visible_buildings(user)
    return Appointment.objects.filter(
        Q(user=user) | Q(building__in=visible_buildings)
    ).distinct()


def _manageable_appointments(user):
    if user.is_staff:
        return Appointment.objects.all()
    return Appointment.objects.filter(user=user)


def _booking_initial_schedule(form, appointment=None):
    if form.is_bound and form.data.get('date'):
        time_raw = form.data.get('time', '')
        return form.data.get('date'), time_raw[:5] if time_raw else ''

    if appointment:
        return appointment.date.isoformat(), appointment.time.strftime('%H:%M')

    return '', ''


def _booking_context(form, *, booking_mode, appointment=None):
    services = Service.objects.filter(is_active=True)
    buildings_data = []
    if 'building' in form.fields:
        buildings_data = [
            {'id': building.id, 'name': building.name, 'address': building.address}
            for building in form.fields['building'].queryset
        ]

    initial_date, initial_time = _booking_initial_schedule(form, appointment)

    membership_credits = []
    membership_by_service = {}
    booking_user = getattr(form, 'booking_user', None)
    if booking_user and booking_user.is_authenticated:
        membership_credits = membership_credit_summary(booking_user)
        for service in services:
            subscription = find_membership_for_booking(
                booking_user,
                service,
                exclude_appointment_id=appointment.pk if appointment else None,
            )
            membership_by_service[str(service.pk)] = bool(subscription)

    return {
        'form': form,
        'booking_mode': booking_mode,
        'appointment': appointment,
        'booking_services': [
            {
                'id': service.id,
                'name': service.name,
                'description': service.description,
                'price': str(service.price),
                'duration_minutes': service.duration_minutes,
                'covered_by_membership': membership_by_service.get(str(service.id), False),
            }
            for service in services
        ],
        'booking_membership_credits': membership_credits,
        'booking_buildings': buildings_data,
        'initial_date': initial_date,
        'initial_time': initial_time,
        'fixed_building_id': (
            appointment.building_id
            if appointment and booking_mode == 'reschedule'
            else ''
        ),
        'timezone_label': 'Ciudad de Guatemala',
    }


@login_required
@require_GET
def availability_api(request):
    building = get_object_or_404(Building, pk=request.GET.get('building'))
    exclude_id = request.GET.get('exclude') or None

    date_param = request.GET.get('date')
    if date_param:
        from datetime import date as date_cls

        appointment_date = date_cls.fromisoformat(date_param)
        slots = get_available_time_slots(building, appointment_date, exclude_id)
        return JsonResponse({'slots': slots})

    year = int(request.GET.get('year', timezone.localdate().year))
    month = int(request.GET.get('month', timezone.localdate().month))
    dates = get_available_dates_in_month(building, year, month, exclude_id)
    return JsonResponse({'dates': dates})


@login_required
def appointment_list(request):
    appointments = (
        _visible_appointments(request.user)
        .select_related('building', 'service', 'user')
    )
    manageable_appointment_ids = set(
        _manageable_appointments(request.user).values_list('pk', flat=True)
    )
    return render(
        request,
        'appointments/appointment_list.html',
        {
            'appointments': appointments,
            'manageable_appointment_ids': manageable_appointment_ids,
        },
    )


@login_required
def appointment_create(request):
    bookable_buildings = _bookable_buildings(request.user)
    if request.method == 'POST':
        form = AppointmentForm(
            request.POST,
            buildings=bookable_buildings,
            booking_ui=True,
            user=request.user,
            allow_recurrence=True,
        )
        if form.is_valid():
            created = form.save_series(request.user)
            skipped = len(getattr(form, 'unavailable_slots', []) or [])
            if len(created) == 1 and not skipped:
                messages.success(request, 'Tu cita fue agendada correctamente.')
            elif skipped:
                messages.success(
                    request,
                    f'Se agendaron {len(created)} cita(s) disponible(s). '
                    f'Se omitieron {skipped} fecha(s) no disponible(s).',
                )
            else:
                messages.success(
                    request,
                    f'Se agendaron {len(created)} citas correctamente.',
                )
            return redirect('appointment_list')
    else:
        form = AppointmentForm(
            buildings=bookable_buildings,
            booking_ui=True,
            user=request.user,
            allow_recurrence=True,
        )

    context = _booking_context(form, booking_mode='create')
    context.update(
        {
            'page_title': 'Agendar cita',
            'submit_label': 'Confirmar cita',
            'initial_service': request.GET.get('service', ''),
        }
    )
    return render(request, 'appointments/appointment_wizard.html', context)


@login_required
def appointment_update(request, pk):
    bookable_buildings = _bookable_buildings(request.user)
    appointment = get_object_or_404(_manageable_appointments(request.user), pk=pk)
    if appointment.status == AppointmentStatus.CANCELLED:
        messages.error(request, 'No puedes editar una cita cancelada.')
        return redirect('appointment_list')
    if request.method == 'POST':
        form = AppointmentForm(
            request.POST,
            instance=appointment,
            buildings=bookable_buildings,
            booking_ui=True,
            user=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'La cita fue actualizada correctamente.')
            return redirect('appointment_list')
    else:
        form = AppointmentForm(
            instance=appointment,
            buildings=bookable_buildings,
            booking_ui=True,
            user=request.user,
        )

    context = _booking_context(form, booking_mode='edit', appointment=appointment)
    context.update(
        {
            'page_title': 'Editar cita',
            'submit_label': 'Guardar cambios',
        }
    )
    return render(request, 'appointments/appointment_booking.html', context)


@login_required
def appointment_reschedule(request, pk):
    appointment = get_object_or_404(_manageable_appointments(request.user), pk=pk)
    if appointment.status == AppointmentStatus.CANCELLED:
        messages.error(request, 'No puedes reagendar una cita cancelada.')
        return redirect('appointment_list')
    if request.method == 'POST':
        form = AppointmentRescheduleForm(
            request.POST,
            instance=appointment,
            booking_ui=True,
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'La cita fue reagendada correctamente.')
            return redirect('appointment_list')
    else:
        form = AppointmentRescheduleForm(instance=appointment, booking_ui=True)

    context = _booking_context(form, booking_mode='reschedule', appointment=appointment)
    context.update(
        {
            'page_title': 'Reagendar cita',
            'submit_label': 'Confirmar cambio',
        }
    )
    return render(request, 'appointments/appointment_booking.html', context)


@login_required
def appointment_cancel(request, pk):
    appointment = get_object_or_404(_manageable_appointments(request.user), pk=pk)
    if request.method == 'POST':
        if appointment.status == AppointmentStatus.CANCELLED:
            messages.info(request, 'Esta cita ya estaba cancelada.')
        else:
            appointment.status = AppointmentStatus.CANCELLED
            appointment.save(update_fields=['status'])
            messages.success(request, 'La cita fue cancelada correctamente.')
        return redirect('appointment_list')

    return render(
        request,
        'appointments/appointment_cancel.html',
        {'appointment': appointment},
    )


@login_required
def appointment_review(request, pk):
    appointment = get_object_or_404(_manageable_appointments(request.user), pk=pk)

    if appointment.status == AppointmentStatus.CANCELLED:
        messages.error(request, 'No puedes calificar una cita cancelada.')
        return redirect('appointment_list')
    if not appointment.is_past:
        messages.error(request, 'Solo puedes calificar después de la fecha de la cita.')
        return redirect('appointment_list')
    if appointment.is_reviewed:
        messages.info(request, 'Esta cita ya fue calificada.')
        return redirect('appointment_list')

    if request.method == 'POST':
        form = AppointmentReviewForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gracias por tu calificación.')
            return redirect('appointment_list')
    else:
        form = AppointmentReviewForm(instance=appointment)

    return render(
        request,
        'appointments/appointment_review.html',
        {
            'appointment': appointment,
            'form': form,
        },
    )


@staff_member_required
def appointment_payment(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related('building', 'service', 'user'),
        pk=pk,
    )

    if request.method == 'POST':
        form = AppointmentPaymentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            if form.cleaned_data.get('is_paid'):
                messages.success(request, 'Pago registrado correctamente.')
            else:
                messages.success(request, 'La cita quedó marcada como pendiente de pago.')
            return redirect('appointment_list')
    else:
        form = AppointmentPaymentForm(instance=appointment)

    return render(
        request,
        'appointments/appointment_payment.html',
        {
            'appointment': appointment,
            'form': form,
        },
    )
