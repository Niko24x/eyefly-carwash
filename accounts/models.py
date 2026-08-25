from django.conf import settings
from django.db import models

from .country_codes import DEFAULT_COUNTRY_CODE


from .phone_utils import format_local_phone_display


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='usuario',
    )
    phone_country_code = models.CharField(
        'código de país',
        max_length=4,
        default=DEFAULT_COUNTRY_CODE,
    )
    phone_number = models.CharField(
        'número de teléfono',
        max_length=15,
        blank=True,
    )
    car_brand = models.CharField('marca del auto', max_length=80, blank=True)
    car_model = models.CharField('modelo', max_length=80, blank=True)
    car_color = models.CharField('color', max_length=40, blank=True)
    car_plate = models.CharField('placa', max_length=20, blank=True)
    parking_level = models.CharField('sótano', max_length=40, blank=True)
    parking_number = models.CharField('número de parqueo', max_length=40, blank=True)

    class Meta:
        verbose_name = 'perfil de usuario'
        verbose_name_plural = 'perfiles de usuario'

    def __str__(self):
        return f'Perfil de {self.user.username}'

    @property
    def formatted_phone(self):
        if not self.phone_number:
            return ''
        local_display = format_local_phone_display(self.phone_number, self.phone_country_code)
        return f'+{self.phone_country_code} {local_display}'


class Vehicle(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name='usuario',
    )
    brand = models.CharField('marca del auto', max_length=80)
    model = models.CharField('modelo', max_length=80)
    color = models.CharField('color', max_length=40)
    plate = models.CharField('placa', max_length=20)
    parking_level = models.CharField('sótano', max_length=40)
    parking_number = models.CharField('número de parqueo', max_length=40)
    is_default = models.BooleanField('predeterminado', default=False)
    created_at = models.DateTimeField('fecha de registro', auto_now_add=True)
    updated_at = models.DateTimeField('fecha de actualización', auto_now=True)

    class Meta:
        ordering = ['-is_default', 'brand', 'model', 'plate']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'plate'],
                name='unique_vehicle_plate_per_user',
            ),
        ]
        verbose_name = 'vehículo'
        verbose_name_plural = 'vehículos'

    def __str__(self):
        return f'{self.brand} {self.model} ({self.plate})'
