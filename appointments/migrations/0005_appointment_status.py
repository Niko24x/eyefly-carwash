import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('appointments', '0004_alter_appointment_created_at_alter_appointment_email_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='appointments',
                to=settings.AUTH_USER_MODEL,
                verbose_name='creada por',
            ),
        ),
        migrations.AddField(
            model_name='appointment',
            name='status',
            field=models.CharField(
                choices=[('active', 'Activa'), ('cancelled', 'Cancelada')],
                default='active',
                max_length=20,
                verbose_name='estado',
            ),
        ),
    ]
