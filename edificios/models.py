from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Building(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_buildings',
        verbose_name='registrado por',
    )
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='admin_buildings',
        verbose_name='administradores',
    )
    name = models.CharField('nombre del edificio', max_length=150)
    address = models.TextField('dirección')
    contact_name = models.CharField('contacto', max_length=150)
    phone_number = models.CharField('número de teléfono', max_length=20)
    email = models.EmailField('correo electrónico')
    notes = models.TextField('notas', blank=True)
    image = models.ImageField(
        'imagen',
        upload_to='buildings/',
        blank=True,
        null=True,
        help_text='Si se agrega, se muestra en la tarjeta del edificio en el inicio.',
    )
    accepts_appointments = models.BooleanField(
        'acepta citas',
        default=True,
        help_text='Si está desactivado, no se podrán agendar nuevas citas en este edificio.',
    )
    autos_por_turno = models.PositiveIntegerField(
        'autos por turno',
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Cantidad de autos que se pueden lavar al mismo tiempo en este edificio.',
    )
    created_at = models.DateTimeField('fecha de registro', auto_now_add=True)
    updated_at = models.DateTimeField('fecha de actualización', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'edificio'
        verbose_name_plural = 'edificios'

    def __str__(self):
        return self.name
