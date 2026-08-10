from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edificios', '0004_building_accepts_appointments'),
    ]

    operations = [
        migrations.AddField(
            model_name='building',
            name='autos_por_turno',
            field=models.PositiveIntegerField(
                default=1,
                help_text='Cantidad de autos que se pueden lavar al mismo tiempo en este edificio.',
                verbose_name='autos por turno',
            ),
        ),
    ]
