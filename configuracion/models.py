from django.db import models


class SystemSettings(models.Model):
    class SlotInterval(models.IntegerChoices):
        FIFTEEN = 15, 'Cada 15 minutos'
        THIRTY = 30, 'Cada 30 minutos'
        SIXTY = 60, 'Cada 60 minutos'

    max_concurrent_appointments = models.PositiveIntegerField(
        'citas simultáneas máximas',
        default=1,
        help_text='Número máximo de citas que se pueden atender a la misma hora.',
    )
    max_advance_booking_days = models.PositiveIntegerField(
        'anticipación máxima en días',
        default=30,
        help_text='Cantidad máxima de días hacia adelante en los que se pueden agendar citas.',
    )
    slot_interval_minutes = models.PositiveSmallIntegerField(
        'intervalo de horarios',
        choices=SlotInterval.choices,
        default=SlotInterval.THIRTY,
        help_text='Define cada cuántos minutos se muestran horarios disponibles para agendar.',
    )

    class Meta:
        verbose_name = 'configuración del sistema'
        verbose_name_plural = 'configuración del sistema'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Configuración del sistema'


class Holiday(models.Model):
    date = models.DateField('fecha', unique=True)
    name = models.CharField('nombre', max_length=150)

    class Meta:
        ordering = ['date']
        verbose_name = 'día festivo'
        verbose_name_plural = 'días festivos'

    def __str__(self):
        return f'{self.name} ({self.date})'


class BuildingSchedule(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, 'Lunes'
        TUESDAY = 1, 'Martes'
        WEDNESDAY = 2, 'Miércoles'
        THURSDAY = 3, 'Jueves'
        FRIDAY = 4, 'Viernes'
        SATURDAY = 5, 'Sábado'
        SUNDAY = 6, 'Domingo'

    building = models.ForeignKey(
        'edificios.Building',
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='edificio',
    )
    day_of_week = models.IntegerField('día de la semana', choices=Weekday.choices)
    start_time = models.TimeField('hora de inicio')
    end_time = models.TimeField('hora de fin')
    is_active = models.BooleanField('activo', default=True)

    class Meta:
        ordering = ['day_of_week']
        unique_together = ['building', 'day_of_week']
        verbose_name = 'horario de edificio'
        verbose_name_plural = 'horarios de edificios'

    def __str__(self):
        return f'{self.building.name} - {self.get_day_of_week_display()}'
