import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('edificios', '0002_building_admins_created_by'),
        ('appointments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='building',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='appointments',
                to='edificios.building',
                verbose_name='edificio',
            ),
        ),
        migrations.AlterField(
            model_name='appointment',
            name='building',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='appointments',
                to='edificios.building',
                verbose_name='edificio',
            ),
        ),
    ]
