from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from configuracion.models import BuildingSchedule, Holiday, SystemSettings
from edificios.models import Building
from membresia.models import MembershipPlan, MembershipSubscription, MembershipSubscriptionStatus
from servicios.models import Service

from .forms import AppointmentForm
from .models import Appointment
from .recurrence import (
    MAX_RECURRENCE_OCCURRENCES,
    RECURRENCE_MENSUAL,
    RECURRENCE_QUINCENAL,
    RECURRENCE_SEMANAL,
    RECURRENCE_UNICA,
    generate_recurrence_dates,
)


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


class GenerateRecurrenceDatesTests(TestCase):
    def test_unica_returns_start_only(self):
        start = date(2026, 8, 10)
        self.assertEqual(
            generate_recurrence_dates(start, date(2026, 9, 10), RECURRENCE_UNICA),
            [start],
        )

    def test_unica_with_none_end_date(self):
        start = date(2026, 8, 10)
        self.assertEqual(
            generate_recurrence_dates(start, None, RECURRENCE_UNICA),
            [start],
        )

    def test_weekly_same_weekday(self):
        start = date(2026, 8, 10)  # Monday
        end = date(2026, 8, 31)
        dates = generate_recurrence_dates(start, end, RECURRENCE_SEMANAL)
        self.assertEqual(
            dates,
            [date(2026, 8, 10), date(2026, 8, 17), date(2026, 8, 24), date(2026, 8, 31)],
        )
        self.assertTrue(all(d.weekday() == start.weekday() for d in dates))

    def test_weekly_includes_end_when_same_weekday(self):
        start = date(2026, 8, 5)
        end = date(2026, 8, 12)
        self.assertEqual(
            generate_recurrence_dates(start, end, RECURRENCE_SEMANAL),
            [date(2026, 8, 5), date(2026, 8, 12)],
        )

    def test_biweekly_same_weekday_every_fourteen_days(self):
        start = date(2026, 8, 10)  # Monday
        end = date(2026, 9, 7)
        dates = generate_recurrence_dates(start, end, RECURRENCE_QUINCENAL)
        self.assertEqual(
            dates,
            [date(2026, 8, 10), date(2026, 8, 24), date(2026, 9, 7)],
        )
        self.assertTrue(all(d.weekday() == start.weekday() for d in dates))

    def test_monthly_same_day_skips_missing_days(self):
        start = date(2026, 1, 31)
        end = date(2026, 4, 30)
        dates = generate_recurrence_dates(start, end, RECURRENCE_MENSUAL)
        self.assertEqual(dates, [date(2026, 1, 31), date(2026, 3, 31)])

    def test_monthly_regular_day(self):
        start = date(2026, 1, 15)
        end = date(2026, 4, 15)
        self.assertEqual(
            generate_recurrence_dates(start, end, RECURRENCE_MENSUAL),
            [
                date(2026, 1, 15),
                date(2026, 2, 15),
                date(2026, 3, 15),
                date(2026, 4, 15),
            ],
        )

    def test_end_before_start_returns_empty(self):
        self.assertEqual(
            generate_recurrence_dates(
                date(2026, 8, 20),
                date(2026, 8, 10),
                RECURRENCE_SEMANAL,
            ),
            [],
        )

    def test_invalid_start_returns_empty(self):
        self.assertEqual(
            generate_recurrence_dates(None, date(2026, 8, 10), RECURRENCE_SEMANAL),
            [],
        )

    def test_unknown_cadence_returns_start(self):
        start = date(2026, 8, 10)
        self.assertEqual(
            generate_recurrence_dates(start, date(2026, 9, 10), 'otra'),
            [start],
        )

    def test_weekly_respects_max_occurrences(self):
        start = date(2026, 1, 1)
        end = start + timedelta(days=7 * (MAX_RECURRENCE_OCCURRENCES + 10))
        dates = generate_recurrence_dates(start, end, RECURRENCE_SEMANAL)
        self.assertEqual(len(dates), MAX_RECURRENCE_OCCURRENCES)


class AppointmentRecurrenceFormTests(TestCase):
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
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={
                'max_concurrent_appointments': 5,
                'max_advance_booking_days': 90,
            },
        )
        self.service = Service.objects.create(name='Lavado completo')

    def _data(self, **overrides):
        start = timezone.localdate() + timedelta(days=1)
        data = {
            'building': self.building.id,
            'service': self.service.id,
            'first_name': 'Ana',
            'last_name': 'Lopez',
            'phone_country_code': '502',
            'phone_local_number': '55512345',
            'email': 'ana@example.com',
            'date': start.isoformat(),
            'time': '10:00',
            'recurrence': 'unica',
        }
        data.update(overrides)
        return data

    def _form(self, **overrides):
        return AppointmentForm(
            data=self._data(**overrides),
            buildings=Building.objects.filter(id=self.building.id),
            user=self.user,
            allow_recurrence=True,
        )

    def test_unica_creates_single_appointment(self):
        start = timezone.localdate() + timedelta(days=1)
        form = self._form(date=start.isoformat(), recurrence='unica')

        self.assertTrue(form.is_valid(), form.errors)
        created = form.save_series(self.user)
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].date, start)

    def test_weekly_series_creates_multiple_appointments(self):
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=14)
        form = self._form(
            date=start.isoformat(),
            end_date=end.isoformat(),
            recurrence='semanal',
        )

        self.assertTrue(form.is_valid(), form.errors)
        created = form.save_series(self.user)
        self.assertEqual(len(created), 3)
        self.assertEqual(
            list(
                Appointment.objects.filter(user=self.user)
                .order_by('date')
                .values_list('date', flat=True)
            ),
            [start, start + timedelta(days=7), start + timedelta(days=14)],
        )

    def test_biweekly_series_creates_every_two_weeks(self):
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=28)
        form = self._form(
            date=start.isoformat(),
            end_date=end.isoformat(),
            recurrence='quincenal',
        )

        self.assertTrue(form.is_valid(), form.errors)
        created = form.save_series(self.user)
        self.assertEqual(len(created), 3)
        self.assertEqual(
            list(
                Appointment.objects.filter(user=self.user)
                .order_by('date')
                .values_list('date', flat=True)
            ),
            [start, start + timedelta(days=14), start + timedelta(days=28)],
        )

    def test_monthly_series_creates_same_day_appointments(self):
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=65)
        form = self._form(
            date=start.isoformat(),
            end_date=end.isoformat(),
            recurrence='mensual',
        )

        self.assertTrue(form.is_valid(), form.errors)
        created = form.save_series(self.user)
        self.assertGreaterEqual(len(created), 2)
        self.assertTrue(all(item.date.day == start.day for item in created))

    def test_requires_end_date_for_weekly(self):
        form = self._form(recurrence='semanal')

        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_requires_end_date_for_monthly(self):
        form = self._form(recurrence='mensual')

        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_rejects_end_date_before_start(self):
        start = timezone.localdate() + timedelta(days=10)
        end = start - timedelta(days=1)
        form = self._form(
            date=start.isoformat(),
            end_date=end.isoformat(),
            recurrence='semanal',
        )

        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)

    def test_rejects_range_without_repetitions(self):
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=3)
        form = self._form(
            date=start.isoformat(),
            end_date=end.isoformat(),
            recurrence='semanal',
        )

        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)
        self.assertIn('no hay repeticiones', str(form.errors['end_date']))

    def test_edit_form_does_not_expose_recurrence_fields(self):
        appointment = Appointment.objects.create(
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
        form = AppointmentForm(
            instance=appointment,
            buildings=Building.objects.filter(id=self.building.id),
            user=self.user,
            allow_recurrence=True,
        )

        self.assertNotIn('recurrence', form.fields)
        self.assertNotIn('end_date', form.fields)
        self.assertNotIn('create_available_only', form.fields)

    def test_holiday_in_series_marks_slot_unavailable(self):
        start = timezone.localdate() + timedelta(days=1)
        holiday = start + timedelta(days=7)
        end = start + timedelta(days=14)
        Holiday.objects.create(date=holiday, name='Festivo de prueba')

        form = self._form(
            date=start.isoformat(),
            end_date=end.isoformat(),
            recurrence='semanal',
        )

        self.assertFalse(form.is_valid())
        unavailable_dates = {item['date'] for item in form.unavailable_slots}
        self.assertIn(holiday, unavailable_dates)
        self.assertIn(start, form.available_dates)
        self.assertIn(end, form.available_dates)

    def test_partial_series_asks_before_creating_available(self):
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={
                'max_concurrent_appointments': 5,
                'max_advance_booking_days': 14,
            },
        )
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=28)
        form = self._form(
            date=start.isoformat(),
            end_date=end.isoformat(),
            recurrence='semanal',
        )

        self.assertFalse(form.is_valid())
        self.assertTrue(form.unavailable_slots)
        self.assertTrue(form.available_dates)
        self.assertIn('No se pueden crear todas las citas', str(form.non_field_errors()))
        self.assertTrue(
            all('label' in item and 'reason' in item for item in form.unavailable_slots)
        )

    def test_create_available_only_creates_partial_series(self):
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={
                'max_concurrent_appointments': 5,
                'max_advance_booking_days': 14,
            },
        )
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=28)
        form = self._form(
            date=start.isoformat(),
            end_date=end.isoformat(),
            recurrence='semanal',
            create_available_only=True,
        )

        self.assertTrue(form.is_valid(), form.errors)
        created = form.save_series(self.user)
        self.assertGreaterEqual(len(created), 1)
        self.assertTrue(form.unavailable_slots)
        self.assertEqual(len(created), len(form.available_dates))
        self.assertTrue(
            all(
                (appointment.date - timezone.localdate()).days <= 14
                for appointment in created
            )
        )

    def test_all_unavailable_rejects_even_with_create_available_only(self):
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={
                'max_concurrent_appointments': 5,
                'max_advance_booking_days': 1,
            },
        )
        start = timezone.localdate() + timedelta(days=3)
        end = start + timedelta(days=7)
        form = self._form(
            date=start.isoformat(),
            end_date=end.isoformat(),
            recurrence='semanal',
            create_available_only=True,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('Ninguna de las fechas', str(form.errors))

    def test_membership_limit_blocks_full_series(self):
        plan = MembershipPlan.objects.create(
            name='Silver',
            tier_label='Silver',
            monthly_price=249,
            monthly_wash_limit=1,
            display_order=1,
        )
        plan.services.add(self.service)
        today = timezone.localdate()
        MembershipSubscription.objects.create(
            user=self.user,
            plan=plan,
            status=MembershipSubscriptionStatus.ACTIVE,
            current_period_start=today.replace(day=1),
            current_period_end=today + timedelta(days=40),
        )

        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=14)
        form = self._form(
            date=start.isoformat(),
            end_date=end.isoformat(),
            recurrence='semanal',
        )

        self.assertFalse(form.is_valid())
        self.assertIn('membresía', str(form.errors).lower())


class AppointmentRecurrenceViewTests(TestCase):
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
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={
                'max_concurrent_appointments': 5,
                'max_advance_booking_days': 90,
            },
        )
        self.service = Service.objects.create(name='Lavado completo')

    def _data(self, **overrides):
        start = timezone.localdate() + timedelta(days=1)
        data = {
            'building': self.building.id,
            'service': self.service.id,
            'first_name': 'Ana',
            'last_name': 'Lopez',
            'full_name': 'Ana Lopez',
            'phone_country_code': '502',
            'phone_local_number': '55512345',
            'email': 'ana@example.com',
            'car_brand': 'Toyota',
            'car_model': 'Corolla',
            'car_color': 'Blanco',
            'car_plate': 'P-123ABC',
            'parking_level': 'S1',
            'parking_number': 'A-12',
            'notes': '',
            'date': start.isoformat(),
            'time': '10:00',
            'recurrence': 'unica',
        }
        data.update(overrides)
        return data

    def test_create_page_includes_recurrence_fields(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.get(reverse('appointment_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Frecuencia')
        self.assertContains(response, 'Solo esta vez')
        self.assertContains(response, 'Cada 15 días')
        self.assertContains(response, 'name="recurrence"')
        self.assertContains(response, 'name="end_date"')
        self.assertContains(response, 'Datos de tu vehículo')
        self.assertContains(response, 'name="car_brand"')
        self.assertContains(response, 'Información de parqueo')

    def test_create_view_weekly_series(self):
        self.client.login(username='cliente', password='password123')
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=7)

        response = self.client.post(
            reverse('appointment_create'),
            self._data(
                date=start.isoformat(),
                end_date=end.isoformat(),
                recurrence='semanal',
            ),
        )

        self.assertRedirects(response, reverse('appointment_list'))
        self.assertEqual(Appointment.objects.filter(first_name='Ana').count(), 2)

    def test_partial_view_lists_unavailable_and_asks_confirmation(self):
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={
                'max_concurrent_appointments': 5,
                'max_advance_booking_days': 14,
            },
        )
        self.client.login(username='cliente', password='password123')
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=28)

        response = self.client.post(
            reverse('appointment_create'),
            self._data(
                date=start.isoformat(),
                end_date=end.isoformat(),
                recurrence='semanal',
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se pueden crear todas las citas.')
        self.assertContains(response, 'Fechas no disponibles:')
        self.assertContains(response, 'Sí se pueden crear')
        self.assertContains(response, '¿Quieres crear solo las citas disponibles?')
        self.assertContains(response, 'Sí, crear las disponibles')
        self.assertContains(response, 'name="create_available_only"')
        self.assertEqual(Appointment.objects.count(), 0)

    def test_confirm_available_only_creates_and_reports_skipped(self):
        SystemSettings.objects.update_or_create(
            pk=1,
            defaults={
                'max_concurrent_appointments': 5,
                'max_advance_booking_days': 14,
            },
        )
        self.client.login(username='cliente', password='password123')
        start = timezone.localdate() + timedelta(days=1)
        end = start + timedelta(days=28)

        response = self.client.post(
            reverse('appointment_create'),
            self._data(
                date=start.isoformat(),
                end_date=end.isoformat(),
                recurrence='semanal',
                create_available_only='1',
            ),
            follow=True,
        )

        created_count = Appointment.objects.filter(first_name='Ana').count()
        self.assertGreaterEqual(created_count, 1)
        self.assertLess(created_count, 5)
        self.assertRedirects(response, reverse('appointment_list'))
        self.assertContains(response, 'disponible')
        self.assertContains(response, 'omitieron')
