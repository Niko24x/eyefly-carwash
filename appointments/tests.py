from datetime import date, datetime, time, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from configuracion.models import BuildingSchedule, Holiday, SystemSettings
from edificios.models import Building
from servicios.models import Service

from .forms import AppointmentForm
from .models import Appointment, AppointmentStatus


User = get_user_model()
GUATEMALA_TZ = ZoneInfo('America/Guatemala')


def _next_weekday(weekday):
    today = timezone.localdate()
    days_ahead = (weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def guatemala_datetime(year, month, day, hour, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=GUATEMALA_TZ)


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


class AppointmentFormTests(TestCase):
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
        self.building.admins.add(self.user)
        _activate_all_schedules(self.building)
        SystemSettings.load()
        self.service = Service.objects.create(
            name='Lavado completo',
            description='Lavado exterior e interior.',
        )

    def _form_data(self, appointment_time, appointment_date=None):
        if appointment_date is None:
            appointment_date = timezone.localdate() + timedelta(days=1)
        if not isinstance(appointment_date, str):
            appointment_date = appointment_date.isoformat()

        return {
            'building': self.building.id,
            'service': self.service.id,
            'first_name': 'Ana',
            'last_name': 'Lopez',
            'phone_country_code': '502',
            'phone_local_number': '55512345',
            'email': 'ana@example.com',
            'date': appointment_date,
            'time': appointment_time,
        }

    def test_accepts_exact_hour(self):
        form = AppointmentForm(
            data=self._form_data('10:00'),
            buildings=Building.objects.filter(id=self.building.id),
        )

        self.assertTrue(form.is_valid())

    def test_accepts_half_hour(self):
        form = AppointmentForm(
            data=self._form_data('10:30'),
            buildings=Building.objects.filter(id=self.building.id),
        )

        self.assertTrue(form.is_valid())

    def test_rejects_random_minutes(self):
        form = AppointmentForm(
            data=self._form_data('10:07'),
            buildings=Building.objects.filter(id=self.building.id),
        )

        self.assertFalse(form.is_valid())
        self.assertIn('time', form.errors)

    def test_rejects_holiday_date(self):
        target_date = timezone.localdate() + timedelta(days=2)
        Holiday.objects.create(date=target_date, name='Día festivo')

        form = AppointmentForm(
            data=self._form_data('10:00', target_date),
            buildings=Building.objects.filter(id=self.building.id),
        )

        self.assertFalse(form.is_valid())
        self.assertIn('día festivo', str(form.errors))

    def test_rejects_outside_building_schedule(self):
        target_date = _next_weekday(4)
        BuildingSchedule.objects.filter(
            building=self.building,
            day_of_week=4,
        ).update(start_time=time(12, 0), end_time=time(14, 0))

        form = AppointmentForm(
            data=self._form_data('10:00', target_date),
            buildings=Building.objects.filter(id=self.building.id),
        )

        self.assertFalse(form.is_valid())
        self.assertIn('fuera del horario disponible', str(form.errors))

    def test_rejects_deactivated_building(self):
        self.building.accepts_appointments = False
        self.building.save(update_fields=['accepts_appointments'])

        form = AppointmentForm(
            data=self._form_data('10:00'),
            buildings=Building.objects.filter(id=self.building.id),
        )

        self.assertFalse(form.is_valid())
        self.assertIn('no está aceptando nuevas citas', str(form.errors))

    def test_rejects_date_beyond_advance_booking_limit(self):
        from django.utils import timezone
        from zoneinfo import ZoneInfo
        from datetime import datetime

        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={
                'max_concurrent_appointments': 1,
                'max_advance_booking_days': 7,
            },
        )
        too_far = (timezone.localdate() + timedelta(days=8)).isoformat()

        form = AppointmentForm(
            data={
                **self._form_data('10:00'),
                'date': too_far,
            },
            buildings=Building.objects.filter(id=self.building.id),
        )

        self.assertFalse(form.is_valid())
        self.assertIn('días de anticipación', str(form.errors))

    def test_rejects_past_date(self):
        guatemala_now = guatemala_datetime(2026, 6, 12, 10, 0)

        with patch('configuracion.availability._local_now', return_value=guatemala_now):
            form = AppointmentForm(
                data={
                    **self._form_data('10:00', '2026-06-11'),
                },
                buildings=Building.objects.filter(id=self.building.id),
            )
            self.assertFalse(form.is_valid())
            self.assertIn('fechas pasadas', str(form.errors))

    def test_rejects_past_time_on_current_date(self):
        guatemala_now = guatemala_datetime(2026, 6, 12, 10, 0)

        with patch('configuracion.availability._local_now', return_value=guatemala_now):
            form = AppointmentForm(
                data={
                    **self._form_data('09:30', '2026-06-12'),
                },
                buildings=Building.objects.filter(id=self.building.id),
            )
            self.assertFalse(form.is_valid())
            self.assertIn('ya pasaron', str(form.errors))


class AppointmentPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cliente',
            email='cliente@example.com',
            password='password123',
        )
        self.other_user = User.objects.create_user(
            username='otro',
            email='otro@example.com',
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
        self.building.admins.add(self.user)
        self.other_building = Building.objects.create(
            created_by=self.other_user,
            name='Edificio Privado',
            address='Calle Cerrada 99',
            contact_name='Carlos Ruiz',
            phone_number='5557654321',
            email='carlos@example.com',
        )
        self.other_building.admins.add(self.other_user)
        _activate_all_schedules(self.building)
        _activate_all_schedules(self.other_building)
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={'max_concurrent_appointments': 2},
        )
        self.service = Service.objects.create(name='Lavado basico')
        self.appointment = Appointment.objects.create(
            user=self.user,
            building=self.building,
            service=self.service,
            first_name='Ana',
            last_name='Lopez',
            phone_number='5551234567',
            email='ana@example.com',
            date=timezone.localdate() + timedelta(days=7),
            time=time(10, 0),
        )
        Appointment.objects.create(
            user=self.other_user,
            building=self.other_building,
            service=self.service,
            first_name='Carlos',
            last_name='Ruiz',
            phone_number='5557654321',
            email='carlos@example.com',
            date=timezone.localdate() + timedelta(days=7),
            time=time(11, 0),
        )

    def test_appointment_list_requires_login(self):
        response = self.client.get(reverse('appointment_list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/cuentas/login/', response['Location'])

    def test_appointment_list_shows_only_current_users_appointments(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.get(reverse('appointment_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ana Lopez')
        self.assertContains(response, 'Torre Central')
        self.assertNotContains(response, 'Carlos Ruiz')

    def test_appointment_create_page_requires_login(self):
        response = self.client.get(reverse('appointment_create'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/cuentas/login/', response['Location'])

    def test_appointment_create_page_renders_for_logged_in_user(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.get(reverse('appointment_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AGENDAR LAVADO')

    def test_appointment_create_assigns_logged_in_user(self):
        self.client.login(username='cliente', password='password123')

        future_date = (timezone.localdate() + timedelta(days=1)).isoformat()
        response = self.client.post(
            reverse('appointment_create'),
            {
                'first_name': 'Maria',
                'building': self.building.id,
                'service': self.service.id,
                'last_name': 'Diaz',
                'full_name': 'Maria Diaz',
                'phone_country_code': '502',
                'phone_local_number': '55511122',
                'email': 'maria@example.com',
                'car_brand': 'Toyota',
                'car_model': 'Corolla',
                'car_color': 'Blanco',
                'car_plate': 'ABC-123',
                'parking_level': 'S1',
                'parking_number': 'A-12',
                'notes': '',
                'date': future_date,
                'time': '09:30',
                'recurrence': 'unica',
            },
        )

        self.assertRedirects(response, reverse('appointment_list'))
        created = Appointment.objects.get(first_name='Maria')
        self.assertEqual(created.user, self.user)
        self.assertEqual(created.building, self.building)
        self.assertEqual(created.phone_number, '50255511122')
        self.assertEqual(created.car_brand, 'Toyota')
        self.assertEqual(created.parking_number, 'A-12')
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.car_plate, 'ABC-123')

    def test_building_admin_can_review_appointments_for_their_building(self):
        self.building.admins.add(self.other_user)
        self.client.login(username='otro', password='password123')

        response = self.client.get(reverse('appointment_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ana Lopez')
        self.assertContains(response, 'Torre Central')

    def test_appointment_create_rejects_random_minutes(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.post(
            reverse('appointment_create'),
            {
                'first_name': 'Maria',
                'building': self.building.id,
                'service': self.service.id,
                'last_name': 'Diaz',
                'full_name': 'Maria Diaz',
                'phone_country_code': '502',
                'phone_local_number': '55511122',
                'email': 'maria@example.com',
                'car_brand': 'Toyota',
                'car_model': 'Corolla',
                'car_color': 'Blanco',
                'car_plate': 'ABC-123',
                'parking_level': 'S1',
                'parking_number': 'A-12',
                'date': '2026-06-13',
                'time': '09:07',
                'recurrence': 'unica',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Selecciona una hora exacta o media hora')
        self.assertFalse(Appointment.objects.filter(first_name='Maria').exists())

    def test_appointment_update_page_requires_login(self):
        response = self.client.get(
            reverse('appointment_update', args=[self.appointment.id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/cuentas/login/', response['Location'])

    def test_appointment_update_updates_visible_appointment(self):
        self.client.login(username='cliente', password='password123')

        future_date = (timezone.localdate() + timedelta(days=1)).isoformat()
        response = self.client.post(
            reverse('appointment_update', args=[self.appointment.id]),
            {
                'first_name': 'Ana',
                'building': self.building.id,
                'service': self.service.id,
                'last_name': 'Martinez',
                'phone_country_code': '502',
                'phone_local_number': '55512345',
                'email': 'ana@example.com',
                'date': future_date,
                'time': '10:30',
            },
        )

        self.assertRedirects(response, reverse('appointment_list'))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.last_name, 'Martinez')

    def test_building_admin_cannot_reschedule_other_users_appointment(self):
        self.building.admins.add(self.other_user)
        self.client.login(username='otro', password='password123')

        response = self.client.get(
            reverse('appointment_reschedule', args=[self.appointment.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_creator_can_reschedule_appointment(self):
        self.client.login(username='cliente', password='password123')

        future_date = (timezone.localdate() + timedelta(days=2)).isoformat()
        response = self.client.post(
            reverse('appointment_reschedule', args=[self.appointment.id]),
            {
                'date': future_date,
                'time': '11:00',
            },
        )

        self.assertRedirects(response, reverse('appointment_list'))
        self.appointment.refresh_from_db()
        self.assertEqual(str(self.appointment.date), future_date)
        self.assertEqual(self.appointment.time, time(11, 0))

    def test_creator_can_cancel_appointment(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.post(
            reverse('appointment_cancel', args=[self.appointment.id])
        )

        self.assertRedirects(response, reverse('appointment_list'))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, AppointmentStatus.CANCELLED)

    def test_building_admin_cannot_cancel_other_users_appointment(self):
        self.building.admins.add(self.other_user)
        self.client.login(username='otro', password='password123')

        response = self.client.post(
            reverse('appointment_cancel', args=[self.appointment.id])
        )

        self.assertEqual(response.status_code, 404)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'active')

    def test_list_shows_creator_and_hides_actions_for_building_admin(self):
        self.building.admins.add(self.other_user)
        self.client.login(username='otro', password='password123')

        response = self.client.get(reverse('appointment_list'))

        self.assertContains(response, 'cliente')
        self.assertNotContains(
            response,
            reverse('appointment_reschedule', args=[self.appointment.id]),
        )
        self.assertNotContains(
            response,
            reverse('appointment_cancel', args=[self.appointment.id]),
        )

    def test_list_shows_reschedule_and_cancel_for_creator(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.get(reverse('appointment_list'))

        self.assertContains(response, 'Reagendar')
        self.assertContains(response, 'Cancelar')
        self.assertContains(
            response,
            reverse('appointment_reschedule', args=[self.appointment.id]),
        )
        self.assertContains(
            response,
            reverse('appointment_cancel', args=[self.appointment.id]),
        )

    def test_past_appointment_can_be_reviewed(self):
        past = Appointment.objects.create(
            user=self.user,
            building=self.building,
            service=self.service,
            first_name='Ana',
            last_name='Lopez',
            phone_number='50255512345',
            email='ana@example.com',
            date=timezone.localdate() - timedelta(days=2),
            time=time(10, 0),
            status=AppointmentStatus.ACTIVE,
        )
        self.client.login(username='cliente', password='password123')

        response = self.client.get(reverse('appointment_list'))
        self.assertContains(response, 'Calificar')
        self.assertContains(response, reverse('appointment_review', args=[past.id]))

        response = self.client.post(
            reverse('appointment_review', args=[past.id]),
            {'rating': '5', 'review_comment': 'Excelente servicio'},
        )
        self.assertRedirects(response, reverse('appointment_list'))
        past.refresh_from_db()
        self.assertEqual(past.rating, 5)
        self.assertEqual(past.review_comment, 'Excelente servicio')
        self.assertIsNotNone(past.reviewed_at)

    def test_future_appointment_cannot_be_reviewed(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.get(
            reverse('appointment_review', args=[self.appointment.id])
        )
        self.assertRedirects(response, reverse('appointment_list'))

        response = self.client.post(
            reverse('appointment_review', args=[self.appointment.id]),
            {'rating': '4', 'review_comment': ''},
        )
        self.assertRedirects(response, reverse('appointment_list'))
        self.appointment.refresh_from_db()
        self.assertIsNone(self.appointment.rating)

    def test_review_comment_is_optional(self):
        past = Appointment.objects.create(
            user=self.user,
            building=self.building,
            service=self.service,
            first_name='Ana',
            last_name='Lopez',
            phone_number='50255512345',
            email='ana@example.com',
            date=timezone.localdate() - timedelta(days=1),
            time=time(11, 0),
            status=AppointmentStatus.ACTIVE,
        )
        self.client.login(username='cliente', password='password123')

        response = self.client.post(
            reverse('appointment_review', args=[past.id]),
            {'rating': '3', 'review_comment': ''},
        )
        self.assertRedirects(response, reverse('appointment_list'))
        past.refresh_from_db()
        self.assertEqual(past.rating, 3)
        self.assertEqual(past.review_comment, '')
