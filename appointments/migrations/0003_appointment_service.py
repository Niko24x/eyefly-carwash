import django.db.models.deletion
from django.db import migrations, models


def create_default_service(apps, schema_editor):
    Service = apps.get_model('servicios', 'Service')
    Appointment = apps.get_model('appointments', 'Appointment')

    default_service, _ = Service.objects.get_or_create(
        name='Lavado general',
        defaults={
            'description': 'Servicio asignado automáticamente a citas existentes.',
        },
    )
    Appointment.objects.filter(service__isnull=True).update(service=default_service)


class Migration(migrations.Migration):

    dependencies = [
        ('servicios', '0001_initial'),
        ('appointments', '0002_appointment_building'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='service',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='appointments',
                to='servicios.service',
                verbose_name='servicio',
            ),
        ),
        migrations.RunPython(create_default_service, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='appointment',
            name='service',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='appointments',
                to='servicios.service',
                verbose_name='servicio',
            ),
        ),
    ]
