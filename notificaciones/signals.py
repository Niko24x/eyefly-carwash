from django.db.models.signals import post_save
from django.dispatch import receiver

from appointments.models import Appointment

from .services import create_appointment_created_notification


@receiver(post_save, sender=Appointment)
def notify_on_appointment_created(sender, instance, created, **kwargs):
    if created:
        create_appointment_created_notification(instance)
