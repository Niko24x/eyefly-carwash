from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0008_appointment_review_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='is_paid',
            field=models.BooleanField(default=False, verbose_name='pagada'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='payment_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('efectivo', 'Efectivo'),
                    ('transferencia', 'Transferencia'),
                    ('tarjeta', 'Tarjeta (Próximamente)'),
                ],
                max_length=20,
                verbose_name='tipo de pago',
            ),
        ),
        migrations.AddField(
            model_name='appointment',
            name='payment_reference',
            field=models.CharField(
                blank=True,
                max_length=120,
                verbose_name='referencia de pago',
            ),
        ),
        migrations.AddField(
            model_name='appointment',
            name='paid_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='fecha de pago',
            ),
        ),
    ]
