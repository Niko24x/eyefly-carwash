# Generated manually for appointment reviews

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0007_appointment_vehicle_parking_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='rating',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(5),
                ],
                verbose_name='calificación',
            ),
        ),
        migrations.AddField(
            model_name='appointment',
            name='review_comment',
            field=models.TextField(blank=True, verbose_name='comentario'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='fecha de reseña'),
        ),
    ]
