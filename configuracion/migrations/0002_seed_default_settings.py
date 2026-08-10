from datetime import time

from django.db import migrations


def seed_defaults(apps, schema_editor):
    Building = apps.get_model('edificios', 'Building')
    BuildingSchedule = apps.get_model('configuracion', 'BuildingSchedule')
    SystemSettings = apps.get_model('configuracion', 'SystemSettings')

    SystemSettings.objects.get_or_create(
        pk=1,
        defaults={'max_concurrent_appointments': 1},
    )

    for building in Building.objects.all():
        for day in range(7):
            BuildingSchedule.objects.get_or_create(
                building=building,
                day_of_week=day,
                defaults={
                    'start_time': time(9, 0),
                    'end_time': time(17, 0),
                    'is_active': day < 5,
                },
            )


class Migration(migrations.Migration):
    dependencies = [
        ('configuracion', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_defaults, migrations.RunPython.noop),
    ]
