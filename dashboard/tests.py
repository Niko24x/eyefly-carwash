from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from appointments.models import Appointment
from edificios.models import Building
from servicios.models import Service


User = get_user_model()


class DashboardTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123',
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            username='cliente',
            first_name='Ana',
            last_name='Lopez',
            email='ana@example.com',
            password='password123',
        )
        self.building = Building.objects.create(
            created_by=self.customer,
            name='Torre Central',
            address='Av. Principal 123',
            contact_name='Ana Lopez',
            phone_number='5551234567',
            email='ana@example.com',
        )
        self.building.admins.add(self.customer)
        self.service = Service.objects.create(name='Lavado completo')
        self.appointment = Appointment.objects.create(
            user=self.customer,
            building=self.building,
            service=self.service,
            first_name='Ana',
            last_name='Lopez',
            phone_number='5551234567',
            email='ana@example.com',
            date=date(2026, 6, 12),
            time=time(10, 30),
        )

    def test_dashboard_requires_staff_user(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.get(reverse('dashboard:index'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_dashboard_downloads_require_staff_user(self):
        self.client.login(username='cliente', password='password123')

        urls = [
            reverse('dashboard:download_users'),
            reverse('dashboard:download_appointments'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 302)
                self.assertIn('/admin/login/', response['Location'])

    def test_staff_user_can_view_dashboard(self):
        self.client.login(username='admin', password='password123')

        response = self.client.get(reverse('dashboard:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard del carwash')
        self.assertContains(response, self.customer.username)
        self.assertContains(response, self.appointment.first_name)
        self.assertContains(response, 'Pagadas')
        self.assertContains(response, 'Pendientes')
        self.assertContains(response, 'Total facturable')
        self.assertEqual(response.context['pending_count'], 1)
        self.assertEqual(response.context['paid_count'], 0)

    def test_staff_can_mark_appointment_as_paid(self):
        self.service.price = 150
        self.service.save(update_fields=['price'])
        self.client.login(username='admin', password='password123')

        response = self.client.post(
            reverse('appointment_payment', args=[self.appointment.id]),
            {
                'is_paid': True,
                'payment_type': 'efectivo',
                'payment_reference': 'CAJA-001',
            },
        )
        self.assertRedirects(response, reverse('appointment_list'))
        self.appointment.refresh_from_db()
        self.assertTrue(self.appointment.is_paid)
        self.assertEqual(self.appointment.payment_type, 'efectivo')
        self.assertEqual(self.appointment.payment_reference, 'CAJA-001')
        self.assertIsNotNone(self.appointment.paid_at)

        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.context['paid_count'], 1)
        self.assertEqual(response.context['pending_count'], 0)
        self.assertEqual(response.context['paid_total'], self.service.price)

    def test_customer_cannot_access_payment_page(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.get(
            reverse('appointment_payment', args=[self.appointment.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_tarjeta_payment_is_not_allowed_yet(self):
        self.client.login(username='admin', password='password123')

        response = self.client.post(
            reverse('appointment_payment', args=[self.appointment.id]),
            {
                'is_paid': True,
                'payment_type': 'tarjeta',
                'payment_reference': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'próximamente')
        self.appointment.refresh_from_db()
        self.assertFalse(self.appointment.is_paid)
    def test_calendar_collapses_days_with_more_than_two_appointments(self):
        Appointment.objects.create(
            user=self.customer,
            building=self.building,
            service=self.service,
            first_name='Bea',
            last_name='Diaz',
            phone_number='5552223333',
            email='bea@example.com',
            date=date(2026, 6, 12),
            time=time(11, 0),
        )
        Appointment.objects.create(
            user=self.customer,
            building=self.building,
            service=self.service,
            first_name='Carlos',
            last_name='Ruiz',
            phone_number='5553334444',
            email='carlos@example.com',
            date=date(2026, 6, 12),
            time=time(12, 0),
        )
        self.client.login(username='admin', password='password123')

        response = self.client.get(reverse('dashboard:index'), {'year': 2026, 'month': 6})

        calendar_day = next(
            day
            for week in response.context['calendar_weeks']
            for day in week
            if day['date'] == date(2026, 6, 12)
        )
        self.assertEqual(len(calendar_day['appointments']), 3)
        self.assertEqual(len(calendar_day['visible_appointments']), 2)
        self.assertEqual(calendar_day['hidden_appointments_count'], 1)
        self.assertContains(response, 'Torre Central')
        self.assertContains(response, 'Ver más (1)')
        self.assertContains(response, 'data-modal="day"')
        self.assertContains(response, 'data-modal="appointment"')
        self.assertContains(response, 'data-appointment-detail')

    def test_staff_user_can_download_users_csv(self):
        self.client.login(username='admin', password='password123')

        response = self.client.get(reverse('dashboard:download_users'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="usuarios.csv"', response['Content-Disposition'])
        content = response.content.decode()
        self.assertIn('usuario,nombre,apellido,correo', content)
        self.assertIn('cliente,Ana,Lopez,ana@example.com', content)

    def test_staff_user_can_download_appointments_csv(self):
        self.client.login(username='admin', password='password123')

        response = self.client.get(reverse('dashboard:download_appointments'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="citas.csv"', response['Content-Disposition'])
        content = response.content.decode()
        self.assertIn(
            'usuario,edificio,nombre,apellido,teléfono,correo,fecha,hora,pagada,tipo_pago,referencia',
            content,
        )
        self.assertIn(
            'cliente,Torre Central,Ana,Lopez,5551234567,ana@example.com,2026-06-12,10:30',
            content,
        )
