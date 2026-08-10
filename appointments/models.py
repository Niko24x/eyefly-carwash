from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone


class AppointmentStatus(models.TextChoices):
    ACTIVE = 'active', 'Activa'
    CANCELLED = 'cancelled', 'Cancelada'


class PaymentType(models.TextChoices):
    EFECTIVO = 'efectivo', 'Efectivo'
    TRANSFERENCIA = 'transferencia', 'Transferencia'
    TARJETA = 'tarjeta', 'Tarjeta (Próximamente)'


class Appointment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='creada por',
    )
    building = models.ForeignKey(
        'edificios.Building',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='edificio',
    )
    service = models.ForeignKey(
        'servicios.Service',
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name='servicio',
    )
    first_name = models.CharField('nombre', max_length=100)
    last_name = models.CharField('apellido', max_length=100)
    phone_number = models.CharField('número de teléfono', max_length=20)
    email = models.EmailField('correo electrónico')
    car_brand = models.CharField('marca del auto', max_length=80, blank=True)
    car_model = models.CharField('modelo', max_length=80, blank=True)
    car_color = models.CharField('color', max_length=40, blank=True)
    car_plate = models.CharField('placa', max_length=20, blank=True)
    parking_level = models.CharField('sótano', max_length=40, blank=True)
    parking_number = models.CharField('número de parqueo', max_length=40, blank=True)
    notes = models.TextField('notas adicionales', blank=True)
    date = models.DateField('fecha')
    time = models.TimeField('hora')
    status = models.CharField(
        'estado',
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.ACTIVE,
    )
    membership_subscription = models.ForeignKey(
        'membresia.MembershipSubscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        verbose_name='membresía aplicada',
    )
    uses_membership = models.BooleanField(
        'cubierta por membresía',
        default=False,
        help_text='Indica que esta cita no requiere pago individual porque usa la suscripción.',
    )
    rating = models.PositiveSmallIntegerField(
        'calificación',
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    review_comment = models.TextField('comentario', blank=True)
    reviewed_at = models.DateTimeField('fecha de reseña', null=True, blank=True)
    is_paid = models.BooleanField('pagada', default=False)
    payment_type = models.CharField(
        'tipo de pago',
        max_length=20,
        choices=PaymentType.choices,
        blank=True,
    )
    payment_reference = models.CharField(
        'referencia de pago',
        max_length=120,
        blank=True,
    )
    paid_at = models.DateTimeField('fecha de pago', null=True, blank=True)
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)

    class Meta:
        ordering = ['date', 'time']
        verbose_name = 'cita'
        verbose_name_plural = 'citas'

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.date} {self.time}'

    @property
    def amount(self):
        if self.uses_membership:
            return 0
        return self.service.price if self.service_id else 0

    @property
    def payment_status_label(self):
        if self.uses_membership:
            return 'Membresía'
        if self.is_paid:
            return 'Pagada'
        return 'Pendiente'

    @property
    def is_past(self):
        return self.date < timezone.localdate()

    @property
    def is_reviewed(self):
        return self.rating is not None

    @property
    def can_be_reviewed(self):
        return (
            self.status == AppointmentStatus.ACTIVE
            and self.is_past
            and not self.is_reviewed
        )
