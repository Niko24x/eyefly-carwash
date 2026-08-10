from django.utils.formats import date_format, time_format

from .models import (
    DeliveryChannel,
    DeliveryStatus,
    Notification,
    NotificationDelivery,
    NotificationEventType,
)


def build_appointment_created_message(appointment):
    appointment = (
        type(appointment)
        .objects.select_related('building', 'service')
        .get(pk=appointment.pk)
    )
    formatted_date = date_format(appointment.date, 'DATE_FORMAT')
    formatted_time = time_format(appointment.time, 'TIME_FORMAT')

    return (
        f'Hola {appointment.first_name} {appointment.last_name},\n\n'
        f'Tu cita de {appointment.service.name} fue agendada correctamente.\n\n'
        f'Edificio: {appointment.building.name}\n'
        f'Fecha: {formatted_date}\n'
        f'Hora: {formatted_time}\n'
        f'Teléfono: {appointment.phone_number}\n'
        f'Correo: {appointment.email}\n\n'
        'Gracias por confiar en Lavado de Autos.'
    )


def create_appointment_created_notification(appointment):
    message = build_appointment_created_message(appointment)
    notification = Notification.objects.create(
        appointment=appointment,
        event_type=NotificationEventType.APPOINTMENT_CREATED,
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


def resend_notification_delivery(notification, channel):
    appointment = notification.appointment
    notification.message = build_appointment_created_message(appointment)
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
    return delivery
