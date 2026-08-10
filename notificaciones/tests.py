from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from appointments.models import Appointment
from edificios.models import Building
from servicios.models import Service

from .models import (
    DeliveryChannel,
    DeliveryStatus,
    Notification,
    NotificationDelivery,
    NotificationEventType,
)
from .services import build_appointment_created_message, create_appointment_created_notification


User = get_user_model()


class NotificationServiceTests(TestCase):
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
        self.service = Service.objects.create(name='Lavado completo')
        self.appointment = Appointment.objects.create(
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

    def test_build_appointment_created_message_includes_appointment_details(self):
        message = build_appointment_created_message(self.appointment)

        self.assertIn('Ana Lopez', message)
        self.assertIn('Lavado completo', message)
        self.assertIn('Torre Central', message)
        self.assertIn('5551234567', message)
        self.assertIn('ana@example.com', message)

    def test_create_appointment_created_notification_creates_pending_deliveries(self):
        appointment = Appointment.objects.create(
            user=self.user,
            building=self.building,
            service=self.service,
            first_name='Maria',
            last_name='Diaz',
            phone_number='5551112222',
            email='maria@example.com',
            date=date(2026, 6, 13),
            time=time(9, 30),
        )
        Notification.objects.filter(appointment=appointment).delete()

        notification = create_appointment_created_notification(appointment)

        self.assertEqual(notification.event_type, NotificationEventType.APPOINTMENT_CREATED)
        self.assertIn('Maria Diaz', notification.message)
        deliveries = NotificationDelivery.objects.filter(notification=notification)
        self.assertEqual(deliveries.count(), 2)

        email_delivery = deliveries.get(channel=DeliveryChannel.EMAIL)
        whatsapp_delivery = deliveries.get(channel=DeliveryChannel.WHATSAPP)

        self.assertEqual(email_delivery.destination, 'maria@example.com')
        self.assertEqual(whatsapp_delivery.destination, '5551112222')
        self.assertEqual(email_delivery.status, DeliveryStatus.PENDING)
        self.assertEqual(whatsapp_delivery.status, DeliveryStatus.PENDING)
        self.assertIsNone(email_delivery.sent_at)
        self.assertIsNone(whatsapp_delivery.sent_at)


class AppointmentNotificationSignalTests(TestCase):
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
        self.service = Service.objects.create(name='Lavado completo')

    def test_appointment_create_triggers_notification(self):
        self.client.login(username='cliente', password='password123')

        target = timezone.localdate() + timedelta(days=1)
        while target.weekday() >= 5:
            target += timedelta(days=1)
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
                'date': target.isoformat(),
                'time': '09:30',
                'recurrence': 'unica',
            },
        )

        self.assertRedirects(response, reverse('appointment_list'))
        appointment = Appointment.objects.get(first_name='Maria')
        self.assertEqual(Notification.objects.filter(appointment=appointment).count(), 1)
        notification = Notification.objects.get(appointment=appointment)

        self.assertEqual(notification.event_type, NotificationEventType.APPOINTMENT_CREATED)
        self.assertEqual(notification.deliveries.count(), 2)
        self.assertTrue(
            notification.deliveries.filter(
                channel=DeliveryChannel.EMAIL,
                destination='maria@example.com',
                status=DeliveryStatus.PENDING,
            ).exists()
        )
        self.assertTrue(
            notification.deliveries.filter(
                channel=DeliveryChannel.WHATSAPP,
                destination='50255511122',
                status=DeliveryStatus.PENDING,
            ).exists()
        )

    def test_appointment_update_does_not_create_notification(self):
        appointment = Appointment.objects.create(
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
        Notification.objects.all().delete()

        self.client.login(username='cliente', password='password123')
        self.client.post(
            reverse('appointment_update', args=[appointment.id]),
            {
                'first_name': 'Ana',
                'building': self.building.id,
                'service': self.service.id,
                'last_name': 'Martinez',
                'phone_country_code': '502',
                'phone_local_number': '55512345',
                'email': 'ana@example.com',
                'date': '2026-06-12',
                'time': '10:30',
            },
        )

        self.assertFalse(Notification.objects.filter(appointment=appointment).exists())


class StaffAppointmentAccessTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123',
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            username='cliente',
            email='cliente@example.com',
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
            time=time(10, 0),
        )

    def test_staff_user_can_open_appointment_edit_page(self):
        self.client.login(username='admin', password='password123')

        response = self.client.get(
            reverse('appointment_update', args=[self.appointment.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editar cita')


class NotificationListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cliente',
            email='cliente@example.com',
            password='password123',
        )
        self.staff_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
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
        self.building.admins.add(self.user)
        self.service = Service.objects.create(name='Lavado completo')
        self.appointment = Appointment.objects.create(
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
        self.notification = Notification.objects.create(
            appointment=self.appointment,
            event_type=NotificationEventType.APPOINTMENT_CREATED,
            message='Nueva cita registrada para Ana Lopez.',
        )
        NotificationDelivery.objects.create(
            notification=self.notification,
            channel=DeliveryChannel.EMAIL,
            destination='ana@example.com',
            status=DeliveryStatus.SENT,
        )
        NotificationDelivery.objects.create(
            notification=self.notification,
            channel=DeliveryChannel.WHATSAPP,
            destination='5551234567',
            status=DeliveryStatus.PENDING,
        )

    def test_notification_list_requires_login(self):
        response = self.client.get(reverse('notification_list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_notification_list_requires_staff_user(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.get(reverse('notification_list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])

    def test_staff_user_can_view_notification_list(self):
        self.client.login(username='admin', password='password123')

        response = self.client.get(reverse('notification_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Notificaciones')
        self.assertContains(response, 'Ana Lopez')
        self.assertContains(response, 'Torre Central')
        self.assertContains(response, 'Lavado completo')
        self.assertContains(response, 'Nueva cita registrada para Ana Lopez.')
        self.assertContains(response, 'ana@example.com')
        self.assertContains(response, '5551234567')
        self.assertContains(response, 'WhatsApp')
        self.assertContains(response, 'delivery-status-pending')
        self.assertContains(response, 'delivery-status-sent')
        self.assertContains(response, 'aria-label="Ver mensaje"')
        self.assertContains(response, 'fa-solid fa-message')
        self.assertContains(response, 'dashboard-table')
        self.assertContains(response, 'aria-label="Editar cita"')
        self.assertContains(response, 'fa-pen')
        self.assertContains(response, 'fa-envelope')
        self.assertContains(response, 'fa-whatsapp')
        self.assertContains(response, 'aria-label="Reenviar correo"')
        self.assertContains(response, 'aria-label="Reenviar WhatsApp"')

    def test_staff_user_can_resend_email_notification(self):
        self.client.login(username='admin', password='password123')
        email_delivery = self.notification.deliveries.get(channel=DeliveryChannel.EMAIL)
        email_delivery.status = DeliveryStatus.SENT
        email_delivery.save(update_fields=['status'])

        response = self.client.post(
            reverse('notification_resend_email', args=[self.notification.pk])
        )

        self.assertRedirects(response, reverse('notification_list'))
        email_delivery.refresh_from_db()
        self.assertEqual(email_delivery.status, DeliveryStatus.PENDING)
        self.assertIsNone(email_delivery.sent_at)

    def test_staff_user_can_resend_whatsapp_notification(self):
        self.client.login(username='admin', password='password123')

        response = self.client.post(
            reverse('notification_resend_whatsapp', args=[self.notification.pk])
        )

        self.assertRedirects(response, reverse('notification_list'))
        whatsapp_delivery = self.notification.deliveries.get(
            channel=DeliveryChannel.WHATSAPP
        )
        self.assertEqual(whatsapp_delivery.status, DeliveryStatus.PENDING)

    def test_resend_requires_staff_user(self):
        self.client.login(username='cliente', password='password123')

        response = self.client.post(
            reverse('notification_resend_email', args=[self.notification.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])
