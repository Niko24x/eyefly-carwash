from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from configuracion.models import BuildingSchedule, Holiday, SystemSettings
from edificios.models import Building
from servicios.models import Service

from .forms import AppointmentRescheduleForm
from .models import Appointment


User = get_user_model()


def _activate_all_schedules(building):
    for day in range(7):
        BuildingSchedule.objects.update_or_create(
            building=building,
            day_of_week=day,
            defaults={
                'start_time': time(8, 0),
                'end_time': time(18, 0),
                'is_active': True,
            },
        )


class AppointmentRescheduleFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cliente',
            email='cliente@example.com',
            password='password123',
        )
        self.building = Building.objects.create(
            created_by=self.user,
            name='Torre Central',
            address='Av. Principal 123',
            contact_name='Ana Lopez',
            phone_number='5551234567',
            email='ana@example.com',
        )
        _activate_all_schedules(self.building)
        SystemSettings.load()
        self.service = Service.objects.create(name='Lavado completo')
        self.appointment = Appointment.objects.create(
            user=self.user,
            building=self.building,
            service=self.service,
            first_name='Ana',
            last_name='Lopez',
            phone_number='50255512345',
            email='ana@example.com',
            date=timezone.localdate() + timedelta(days=1),
            time=time(10, 0),
        )

    def _data(self, appointment_time='11:00', appointment_date=None):
        if appointment_date is None:
            appointment_date = timezone.localdate() + timedelta(days=2)
        if not isinstance(appointment_date, str):
            appointment_date = appointment_date.isoformat()
        return {'date': appointment_date, 'time': appointment_time}

    def test_valid_reschedule(self):
        form = AppointmentRescheduleForm(data=self._data(), instance=self.appointment)

        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_random_minutes(self):
        form = AppointmentRescheduleForm(
            data=self._data(appointment_time='11:07'),
            instance=self.appointment,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('time', form.errors)

    def test_rejects_holiday(self):
        target_date = timezone.localdate() + timedelta(days=3)
        Holiday.objects.create(date=target_date, name='Día festivo')

        form = AppointmentRescheduleForm(
            data=self._data(appointment_date=target_date),
            instance=self.appointment,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('día festivo', str(form.errors))

    def test_rejects_outside_building_schedule(self):
        target_date = timezone.localdate() + timedelta(days=2)
        BuildingSchedule.objects.filter(
            building=self.building,
            day_of_week=target_date.weekday(),
        ).update(start_time=time(12, 0), end_time=time(14, 0))

        form = AppointmentRescheduleForm(
            data=self._data(appointment_time='10:00', appointment_date=target_date),
            instance=self.appointment,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('fuera del horario disponible', str(form.errors))
