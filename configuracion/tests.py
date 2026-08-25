from datetime import date, datetime, time, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from configuracion.availability import get_available_time_slots, validate_appointment_slot
from configuracion.models import BuildingSchedule, Holiday, SystemSettings
from edificios.models import Building
from servicios.models import Service

from appointments.models import Appointment


User = get_user_model()
GUATEMALA_TZ = ZoneInfo('America/Guatemala')


def guatemala_datetime(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=GUATEMALA_TZ)

class AvailabilityValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password123',
            is_staff=True,
        )
        self.building = Building.objects.create(
            created_by=self.user,
            name='Torre Central',
            address='Av. Principal 123',
            contact_name='Ana Lopez',
            phone_number='5551234567',
            email='ana@example.com',
        )
        self.service = Service.objects.create(name='Lavado basico')
        self.long_service = Service.objects.create(
            name='Lavado premium',
            duration_minutes=90,
        )
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={'max_concurrent_appointments': 1},
        )
        BuildingSchedule.objects.filter(building=self.building, day_of_week=4).update(
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True,
        )

    @patch('configuracion.availability._local_now')
    def test_rejects_holiday(self, mock_local_now):
        mock_local_now.return_value = guatemala_datetime(2026, 6, 10, 8, 0)
        Holiday.objects.create(date=date(2026, 6, 12), name='Festivo')

        error = validate_appointment_slot(
            self.building,
            date(2026, 6, 12),
            time(10, 0),
        )

        self.assertIn('día festivo', error)

    @patch('configuracion.availability._local_now')
    def test_rejects_when_building_capacity_is_full(self, mock_local_now):
        mock_local_now.return_value = guatemala_datetime(2026, 6, 10, 8, 0)
        self.building.autos_por_turno = 1
        self.building.save(update_fields=['autos_por_turno'])
        Appointment.objects.create(
            user=self.user,
            building=self.building,
            service=self.service,
            first_name='Ana',
            last_name='Lopez',
            phone_number='5551234567',
            email='ana@example.com',
            date=date(2026, 6, 12),
            time=time(10, 0),
        )

        error = validate_appointment_slot(
            self.building,
            date(2026, 6, 12),
            time(10, 0),
        )

        self.assertIn('espacios disponibles', error)

    @patch('configuracion.availability._local_now')
    def test_allows_slot_when_building_has_remaining_capacity(self, mock_local_now):
        mock_local_now.return_value = guatemala_datetime(2026, 6, 10, 8, 0)
        self.building.autos_por_turno = 2
        self.building.save(update_fields=['autos_por_turno'])
        Appointment.objects.create(
            user=self.user,
            building=self.building,
            service=self.service,
            first_name='Ana',
            last_name='Lopez',
            phone_number='5551234567',
            email='ana@example.com',
            date=date(2026, 6, 12),
            time=time(10, 0),
        )

        error = validate_appointment_slot(
            self.building,
            date(2026, 6, 12),
            time(10, 0),
        )

        self.assertIsNone(error)

    @patch('configuracion.availability._local_now')
    def test_rejects_start_inside_existing_service_duration(self, mock_local_now):
        mock_local_now.return_value = guatemala_datetime(2026, 6, 10, 8, 0)
        self.building.autos_por_turno = 1
        self.building.save(update_fields=['autos_por_turno'])
        Appointment.objects.create(
            user=self.user,
            building=self.building,
            service=self.long_service,
            first_name='Ana',
            last_name='Lopez',
            phone_number='5551234567',
            email='ana@example.com',
            date=date(2026, 6, 12),
            time=time(9, 0),
        )

        error = validate_appointment_slot(
            self.building,
            date(2026, 6, 12),
            time(9, 30),
            service=self.service,
        )

        self.assertIn('espacios disponibles', error)

    @patch('configuracion.availability._local_now')
    def test_allows_start_at_existing_service_end(self, mock_local_now):
        mock_local_now.return_value = guatemala_datetime(2026, 6, 10, 8, 0)
        self.building.autos_por_turno = 1
        self.building.save(update_fields=['autos_por_turno'])
        Appointment.objects.create(
            user=self.user,
            building=self.building,
            service=self.long_service,
            first_name='Ana',
            last_name='Lopez',
            phone_number='5551234567',
            email='ana@example.com',
            date=date(2026, 6, 12),
            time=time(9, 0),
        )

        error = validate_appointment_slot(
            self.building,
            date(2026, 6, 12),
            time(10, 30),
            service=self.service,
        )

        self.assertIsNone(error)

    @patch('configuracion.availability._local_now')
    def test_rejects_long_service_that_would_overlap_existing_start(self, mock_local_now):
        mock_local_now.return_value = guatemala_datetime(2026, 6, 10, 8, 0)
        self.building.autos_por_turno = 1
        self.building.save(update_fields=['autos_por_turno'])
        Appointment.objects.create(
            user=self.user,
            building=self.building,
            service=self.service,
            first_name='Ana',
            last_name='Lopez',
            phone_number='5551234567',
            email='ana@example.com',
            date=date(2026, 6, 12),
            time=time(9, 30),
        )

        error = validate_appointment_slot(
            self.building,
            date(2026, 6, 12),
            time(9, 0),
            service=self.long_service,
        )

        self.assertIn('espacios disponibles', error)

    @patch('configuracion.availability._local_now')
    def test_capacity_is_scoped_per_building(self, mock_local_now):
        mock_local_now.return_value = guatemala_datetime(2026, 6, 10, 8, 0)
        self.building.autos_por_turno = 1
        self.building.save(update_fields=['autos_por_turno'])
        other_building = Building.objects.create(
            created_by=self.user,
            name='Torre Norte',
            address='Calle 2',
            contact_name='Luis',
            phone_number='5559999999',
            email='luis@example.com',
            autos_por_turno=1,
        )
        BuildingSchedule.objects.filter(building=other_building, day_of_week=4).update(
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True,
        )
        Appointment.objects.create(
            user=self.user,
            building=self.building,
            service=self.service,
            first_name='Ana',
            last_name='Lopez',
            phone_number='5551234567',
            email='ana@example.com',
            date=date(2026, 6, 12),
            time=time(10, 0),
        )

        error = validate_appointment_slot(
            other_building,
            date(2026, 6, 12),
            time(10, 0),
        )

        self.assertIsNone(error)

    def test_rejects_date_beyond_advance_booking_limit(self):
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={
                'max_concurrent_appointments': 1,
                'max_advance_booking_days': 7,
            },
        )
        too_far = timezone.localdate() + timedelta(days=8)

        error = validate_appointment_slot(
            self.building,
            too_far,
            time(10, 0),
        )

        self.assertIn('días de anticipación', error)

    def test_rejects_past_date(self):
        guatemala_now = guatemala_datetime(2026, 6, 12, 10, 0)

        with patch('configuracion.availability._local_now', return_value=guatemala_now):
            error = validate_appointment_slot(
                self.building,
                date(2026, 6, 11),
                time(10, 0),
            )

        self.assertIn('fechas pasadas', error)

    def test_rejects_past_time_on_current_date(self):
        guatemala_now = guatemala_datetime(2026, 6, 12, 10, 0)

        with patch('configuracion.availability._local_now', return_value=guatemala_now):
            error = validate_appointment_slot(
                self.building,
                date(2026, 6, 12),
                time(9, 30),
            )

        self.assertIn('ya pasaron', error)

    def test_allows_future_time_on_current_date(self):
        guatemala_now = guatemala_datetime(2026, 6, 12, 10, 0)

        with patch('configuracion.availability._local_now', return_value=guatemala_now):
            error = validate_appointment_slot(
                self.building,
                date(2026, 6, 12),
                time(10, 30),
            )

        self.assertIsNone(error)

    @patch('configuracion.availability._local_now')
    def test_available_slots_use_configured_fifteen_minute_interval(self, mock_local_now):
        mock_local_now.return_value = guatemala_datetime(2026, 6, 10, 8, 0)
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={
                'max_concurrent_appointments': 1,
                'max_advance_booking_days': 30,
                'slot_interval_minutes': 15,
            },
        )

        slots = get_available_time_slots(
            self.building,
            date(2026, 6, 12),
            service=self.service,
        )

        self.assertIn('09:15', slots)
        self.assertIn('09:45', slots)

    @patch('configuracion.availability._local_now')
    def test_available_slots_use_configured_hourly_interval(self, mock_local_now):
        mock_local_now.return_value = guatemala_datetime(2026, 6, 10, 8, 0)
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={
                'max_concurrent_appointments': 1,
                'max_advance_booking_days': 30,
                'slot_interval_minutes': 60,
            },
        )

        slots = get_available_time_slots(
            self.building,
            date(2026, 6, 12),
            service=self.service,
        )

        self.assertIn('09:00', slots)
        self.assertNotIn('09:30', slots)


class ConfiguracionViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password123',
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username='cliente',
            email='cliente@example.com',
            password='password123',
        )

    def test_settings_index_requires_staff(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.get(reverse('configuracion:index'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_settings_index_renders_for_staff(self):
        self.client.login(username='staff', password='password123')

        response = self.client.get(reverse('configuracion:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Configuración')
        self.assertContains(response, 'Días festivos')
        self.assertContains(response, 'Horarios por edificio')

    def test_staff_can_create_holiday(self):
        self.client.login(username='staff', password='password123')

        response = self.client.post(
            reverse('configuracion:holiday_list'),
            {
                'date': '2026-12-25',
                'name': 'Navidad',
            },
        )

        self.assertRedirects(response, reverse('configuracion:holiday_list'))
        self.assertTrue(Holiday.objects.filter(name='Navidad').exists())
