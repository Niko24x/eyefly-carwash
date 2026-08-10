from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edificios', '0005_building_autos_por_turno'),
    ]

    operations = [
        migrations.AddField(
            model_name='building',
            name='image',
            field=models.ImageField(
                blank=True,
                help_text='Si se agrega, se muestra en la tarjeta del edificio en el inicio.',
                null=True,
                upload_to='buildings/',
                verbose_name='imagen',
            ),
        ),
    ]
