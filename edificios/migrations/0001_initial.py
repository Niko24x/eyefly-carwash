# Generated manually for the edificios app.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Building',
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
                (
                    'name',
                    models.CharField(max_length=150, verbose_name='nombre del edificio'),
                ),
                ('address', models.TextField(verbose_name='direccion')),
                (
                    'contact_name',
                    models.CharField(max_length=150, verbose_name='contacto'),
                ),
                (
                    'phone_number',
                    models.CharField(max_length=20, verbose_name='numero de telefono'),
                ),
                ('email', models.EmailField(max_length=254, verbose_name='correo electronico')),
                ('notes', models.TextField(blank=True, verbose_name='notas')),
                (
                    'created_at',
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name='fecha de registro',
                    ),
                ),
                (
                    'updated_at',
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name='fecha de actualizacion',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='buildings',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='usuario',
                    ),
                ),
            ],
            options={
                'verbose_name': 'edificio',
                'verbose_name_plural': 'edificios',
                'ordering': ['-created_at'],
            },
        ),
    ]
