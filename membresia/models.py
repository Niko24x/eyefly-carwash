from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class MembershipPlan(models.Model):
    ACCENT_BLUE = 'blue'
    ACCENT_RED = 'red'
    ACCENT_MIDNIGHT = 'midnight'
    ACCENT_CHOICES = [
        (ACCENT_BLUE, 'Azul'),
        (ACCENT_RED, 'Rojo'),
        (ACCENT_MIDNIGHT, 'Medianoche'),
    ]

    name = models.CharField('nombre', max_length=80)
    tier_label = models.CharField('etiqueta del plan', max_length=40)
    emoji = models.CharField('ícono', max_length=8, blank=True)
    accent = models.CharField(
        'color de la tarjeta',
        max_length=12,
        choices=ACCENT_CHOICES,
        default=ACCENT_BLUE,
    )
    monthly_price = models.DecimalField('precio mensual', max_digits=8, decimal_places=2)
    savings_label = models.CharField('mensaje de ahorro', max_length=120, blank=True)
    features = models.TextField(
        'beneficios',
        blank=True,
        help_text='Un beneficio por línea.',
    )
    monthly_wash_limit = models.PositiveIntegerField(
        'lavados incluidos por mes',
        null=True,
        blank=True,
        help_text='Déjalo vacío para lavados ilimitados dentro de los servicios incluidos.',
    )
    covers_all_services = models.BooleanField(
        'incluye todos los servicios',
        default=False,
    )
    is_featured = models.BooleanField('destacado', default=False)
    featured_banner = models.CharField('banda destacada', max_length=80, blank=True)
    is_available_for_purchase = models.BooleanField(
        'disponible para compra',
        default=False,
        help_text='Si está desactivado, se muestra como "Próximamente".',
    )
    display_order = models.PositiveIntegerField('orden', default=0)
    is_active = models.BooleanField('activo', default=True)
    services = models.ManyToManyField(
        'servicios.Service',
        blank=True,
        related_name='membership_plans',
        verbose_name='servicios incluidos',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'plan de membresía'
        verbose_name_plural = 'planes de membresía'

    def __str__(self):
        return self.name

    def feature_items(self):
        return [line.strip() for line in self.features.splitlines() if line.strip()]


class MembershipSubscriptionStatus(models.TextChoices):
    ACTIVE = 'active', 'Activa'
    CANCELLED = 'cancelled', 'Cancelada'
    EXPIRED = 'expired', 'Expirada'


class MembershipSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='membership_subscriptions',
        verbose_name='usuario',
    )
    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name='plan',
    )
    status = models.CharField(
        'estado',
        max_length=20,
        choices=MembershipSubscriptionStatus.choices,
        default=MembershipSubscriptionStatus.ACTIVE,
    )
    current_period_start = models.DateField('inicio del periodo')
    current_period_end = models.DateField('fin del periodo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-current_period_end', '-created_at']
        verbose_name = 'suscripción de membresía'
        verbose_name_plural = 'suscripciones de membresía'

    def __str__(self):
        return f'{self.user} · {self.plan.name}'
