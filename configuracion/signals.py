from datetime import time

from django.db.models.signals import post_save
from django.dispatch import receiver

from edificios.models import Building

from .models import BuildingSchedule


@receiver(post_save, sender=Building)
def create_default_schedules(sender, instance, created, **kwargs):
    if not created:
        return

    for day in range(7):
        BuildingSchedule.objects.get_or_create(
            building=instance,
            day_of_week=day,
            defaults={
                'start_time': time(9, 0),
                'end_time': time(17, 0),
                'is_active': day < 5,
            },
        )
