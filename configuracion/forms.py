from django import forms
from django.forms import inlineformset_factory

from edificios.models import Building

from .models import BuildingSchedule, Holiday, SystemSettings


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = ['max_concurrent_appointments', 'max_advance_booking_days']
        labels = {
            'max_concurrent_appointments': 'Citas simultáneas máximas',
            'max_advance_booking_days': 'Anticipación máxima (días)',
        }
        help_texts = {
            'max_concurrent_appointments': (
                'Cantidad máxima de citas que se pueden atender a la misma fecha y hora.'
            ),
            'max_advance_booking_days': (
                'Número máximo de días hacia adelante permitidos para agendar una cita.'
            ),
        }


class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ['date', 'name']
        labels = {
            'date': 'Fecha',
            'name': 'Nombre',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'name': forms.TextInput(attrs={'placeholder': 'Ej. Día de la Independencia'}),
        }


class BuildingScheduleDayForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('DELETE'):
            return cleaned_data

        is_active = cleaned_data.get('is_active')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if is_active and start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(
                'La hora de inicio debe ser anterior a la hora de fin.'
            )

        return cleaned_data

    class Meta:
        model = BuildingSchedule
        fields = ['day_of_week', 'is_active', 'start_time', 'end_time']
        labels = {
            'is_active': 'Disponible',
            'start_time': 'Desde',
            'end_time': 'Hasta',
        }
        widgets = {
            'day_of_week': forms.HiddenInput(),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'step': '1800'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'step': '1800'}),
        }


BuildingScheduleFormSet = inlineformset_factory(
    Building,
    BuildingSchedule,
    form=BuildingScheduleDayForm,
    extra=0,
    can_delete=False,
)
