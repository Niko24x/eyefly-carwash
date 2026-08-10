from django.db import migrations


def update_basico_badge(apps, schema_editor):
    Service = apps.get_model('servicios', 'Service')
    Service.objects.filter(name='Básico', badge='ESENCIAL').update(badge='POPULAR')


def revert_basico_badge(apps, schema_editor):
    Service = apps.get_model('servicios', 'Service')
    Service.objects.filter(name='Básico', badge='POPULAR').update(badge='ESENCIAL')


class Migration(migrations.Migration):

    dependencies = [
        ('servicios', '0003_seed_pricing_plans'),
    ]

    operations = [
        migrations.RunPython(update_basico_badge, revert_basico_badge),
    ]
