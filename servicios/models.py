from django.db import models


class Service(models.Model):
    ACCENT_BLUE = 'blue'
    ACCENT_RED = 'red'
    ACCENT_DARK = 'dark'
    ACCENT_CHOICES = [
        (ACCENT_BLUE, 'Azul'),
        (ACCENT_RED, 'Rojo'),
        (ACCENT_DARK, 'Azul oscuro'),
    ]

    name = models.CharField('nombre', max_length=150)
    description = models.TextField('descripción', blank=True)
    price = models.DecimalField('precio', max_digits=8, decimal_places=2, default=0)
    duration_minutes = models.PositiveIntegerField('duración (minutos)', default=30)
    badge = models.CharField(
        'etiqueta',
        max_length=40,
        blank=True,
        help_text='Texto corto que se muestra en la tarjeta, por ejemplo "MÁS VENDIDO".',
    )
    features = models.TextField(
        'características',
        blank=True,
        help_text=(
            'Una característica por línea. Antepón "!" a una línea para mostrarla '
            'como no incluida (tachada).'
        ),
    )
    accent = models.CharField(
        'color de la tarjeta',
        max_length=10,
        choices=ACCENT_CHOICES,
        default=ACCENT_BLUE,
    )
    is_featured = models.BooleanField('destacado', default=False)
    display_order = models.PositiveIntegerField('orden', default=0)
    is_active = models.BooleanField('activo', default=True)
    created_at = models.DateTimeField('fecha de registro', auto_now_add=True)
    updated_at = models.DateTimeField('fecha de actualización', auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'servicio'
        verbose_name_plural = 'servicios'

    def __str__(self):
        return self.name

    def feature_items(self):
        """Parse the ``features`` text into a list of {text, included} dicts."""
        items = []
        for raw_line in self.features.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            included = not line.startswith('!')
            text = line[1:].strip() if line.startswith('!') else line
            if text:
                items.append({'text': text, 'included': included})
        return items
