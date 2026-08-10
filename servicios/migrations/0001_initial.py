from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Service',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('name', models.CharField(max_length=150, verbose_name='nombre')),
                (
                    'description',
                    models.TextField(blank=True, verbose_name='descripcion'),
                ),
                ('is_active', models.BooleanField(default=True, verbose_name='activo')),
                (
                    'created_at',
                    models.DateTimeField(
                        auto_now_add=True, verbose_name='fecha de registro'
                    ),
                ),
                (
                    'updated_at',
                    models.DateTimeField(
                        auto_now=True, verbose_name='fecha de actualizacion'
                    ),
                ),
            ],
            options={
                'verbose_name': 'servicio',
                'verbose_name_plural': 'servicios',
                'ordering': ['name'],
            },
        ),
    ]
