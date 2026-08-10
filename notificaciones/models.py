from django.db import models


class NotificationEventType(models.TextChoices):
    APPOINTMENT_CREATED = 'appointment_created', 'Cita creada'
    APPOINTMENT_UPDATED = 'appointment_updated', 'Cita actualizada'


class DeliveryChannel(models.TextChoices):
    EMAIL = 'email', 'Correo electrónico'
    WHATSAPP = 'whatsapp', 'WhatsApp'


class DeliveryStatus(models.TextChoices):
    PENDING = 'pending', 'Pendiente'
    SENT = 'sent', 'Enviado'
    FAILED = 'failed', 'Fallido'


class Notification(models.Model):
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='cita',
    )
    event_type = models.CharField(
        'tipo de evento',
        max_length=50,
        choices=NotificationEventType.choices,
    )
    message = models.TextField('mensaje')
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'notificación'
        verbose_name_plural = 'notificaciones'

    def __str__(self):
        return f'{self.get_event_type_display()} - cita #{self.appointment_id}'


class NotificationDelivery(models.Model):
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='deliveries',
        verbose_name='notificación',
    )
    channel = models.CharField(
        'canal',
        max_length=20,
        choices=DeliveryChannel.choices,
    )
    destination = models.CharField('destino', max_length=254)
    status = models.CharField(
        'estado',
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
    )
    sent_at = models.DateTimeField('fecha de envío', null=True, blank=True)
    error_message = models.TextField('error', blank=True)
    created_at = models.DateTimeField('fecha de registro', auto_now_add=True)
    updated_at = models.DateTimeField('fecha de actualización', auto_now=True)

    class Meta:
        ordering = ['channel']
        verbose_name = 'envío de notificación'
        verbose_name_plural = 'envíos de notificación'
        constraints = [
            models.UniqueConstraint(
                fields=['notification', 'channel'],
                name='unique_notification_channel',
            ),
        ]

    def __str__(self):
        return f'{self.get_channel_display()} -> {self.destination} ({self.get_status_display()})'
