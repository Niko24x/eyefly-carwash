from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.formats import date_format, time_format

from .models import (
    DeliveryChannel,
    DeliveryStatus,
    Notification,
    NotificationDelivery,
    NotificationEventType,
)


def _load_appointment(appointment):
    return (
        type(appointment)
        .objects.select_related('building', 'service')
        .get(pk=appointment.pk)
    )


def _appointment_details_block(appointment):
    formatted_date = date_format(appointment.date, 'DATE_FORMAT')
    formatted_time = time_format(appointment.time, 'TIME_FORMAT')
    return (
        f'Edificio: {appointment.building.name}\n'
        f'Fecha: {formatted_date}\n'
        f'Hora: {formatted_time}\n'
        f'Teléfono: {appointment.phone_number}\n'
        f'Correo: {appointment.email}\n'
    )


def build_appointment_created_message(appointment):
    appointment = _load_appointment(appointment)
    return (
        f'Hola {appointment.first_name} {appointment.last_name},\n\n'
        f'Tu cita de {appointment.service.name} fue agendada correctamente.\n\n'
        f'{_appointment_details_block(appointment)}\n'
        'Gracias por confiar en Lavado de Autos.'
    )


def build_appointment_updated_message(appointment):
    appointment = _load_appointment(appointment)
    return (
        f'Hola {appointment.first_name} {appointment.last_name},\n\n'
        f'Tu cita de {appointment.service.name} fue actualizada.\n\n'
        f'{_appointment_details_block(appointment)}\n'
        'Gracias por confiar en Lavado de Autos.'
    )


def build_notification_message(appointment, event_type):
    if event_type == NotificationEventType.APPOINTMENT_UPDATED:
        return build_appointment_updated_message(appointment)
    return build_appointment_created_message(appointment)


def email_subject_for_notification(notification):
    appointment = _load_appointment(notification.appointment)
    if notification.event_type == NotificationEventType.APPOINTMENT_UPDATED:
        return f'Tu cita fue actualizada - {appointment.service.name}'
    return f'Confirmación de cita - {appointment.service.name}'


def _create_notification_with_deliveries(appointment, event_type, message):
    notification = Notification.objects.create(
        appointment=appointment,
        event_type=event_type,
        message=message,
    )
    NotificationDelivery.objects.bulk_create(
        [
            NotificationDelivery(
                notification=notification,
                channel=DeliveryChannel.EMAIL,
                destination=appointment.email,
                status=DeliveryStatus.PENDING,
            ),
            NotificationDelivery(
                notification=notification,
                channel=DeliveryChannel.WHATSAPP,
                destination=appointment.phone_number,
                status=DeliveryStatus.PENDING,
            ),
        ]
    )
    return notification


def send_email_delivery(delivery):
    """Send a pending email delivery and update its status."""
    if delivery.channel != DeliveryChannel.EMAIL:
        return delivery

    notification = delivery.notification
    try:
        send_mail(
            subject=email_subject_for_notification(notification),
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[delivery.destination],
            fail_silently=False,
        )
    except Exception as exc:  # noqa: BLE001 - persist any SMTP/transport error
        delivery.status = DeliveryStatus.FAILED
        delivery.sent_at = None
        delivery.error_message = str(exc)[:2000]
        delivery.save(update_fields=['status', 'sent_at', 'error_message', 'updated_at'])
        return delivery

    delivery.status = DeliveryStatus.SENT
    delivery.sent_at = timezone.now()
    delivery.error_message = ''
    delivery.save(update_fields=['status', 'sent_at', 'error_message', 'updated_at'])
    return delivery


def send_notification_email(notification):
    delivery = notification.deliveries.filter(channel=DeliveryChannel.EMAIL).first()
    if delivery is None:
        return None
    return send_email_delivery(delivery)


def create_appointment_created_notification(appointment):
    message = build_appointment_created_message(appointment)
    notification = _create_notification_with_deliveries(
        appointment,
        NotificationEventType.APPOINTMENT_CREATED,
        message,
    )
    send_notification_email(notification)
    return notification


def create_appointment_updated_notification(appointment):
    message = build_appointment_updated_message(appointment)
    notification = _create_notification_with_deliveries(
        appointment,
        NotificationEventType.APPOINTMENT_UPDATED,
        message,
    )
    send_notification_email(notification)
    return notification


def resend_notification_delivery(notification, channel):
    appointment = notification.appointment
    notification.message = build_notification_message(
        appointment,
        notification.event_type,
    )
    notification.save(update_fields=['message'])

    if channel == DeliveryChannel.EMAIL:
        destination = appointment.email
    else:
        destination = appointment.phone_number

    delivery, _created = NotificationDelivery.objects.update_or_create(
        notification=notification,
        channel=channel,
        defaults={
            'destination': destination,
            'status': DeliveryStatus.PENDING,
            'sent_at': None,
            'error_message': '',
        },
    )
    if channel == DeliveryChannel.EMAIL:
        return send_email_delivery(delivery)
    return delivery
