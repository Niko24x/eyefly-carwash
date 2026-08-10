from datetime import date, datetime, time, timedelta
import calendar
from zoneinfo import ZoneInfo

from django.utils import timezone
from appointments.models import Appointment, AppointmentStatus
from configuracion.models import BuildingSchedule, Holiday, SystemSettings


def _half_hour_slots(start_time, end_time):
    slots = []
    current = datetime.combine(date.today(), start_time)
    while current.time() <= end_time:
        slot_time = current.time().replace(second=0, microsecond=0)
        if slot_time.minute in (0, 30):
            slots.append(slot_time)
        current += timedelta(minutes=30)
    return slots


def _booking_date_limits():
    settings = SystemSettings.load()
    today = timezone.localdate()
    max_date = today + timedelta(days=settings.max_advance_booking_days)
    return today, max_date


def _local_now():
    return timezone.localtime()


def validate_appointment_slot(
    building,
    appointment_date,
    appointment_time,
    exclude_appointment_id=None,
):
    if not building.accepts_appointments:
        is_existing_reschedule = False
        if exclude_appointment_id:
            is_existing_reschedule = Appointment.objects.filter(
                pk=exclude_appointment_id,
                building=building,
            ).exists()
        if not is_existing_reschedule:
            return 'Este edificio no está aceptando nuevas citas en este momento.'

    now = _local_now()
    today = now.date()
    current_time = now.time().replace(second=0, microsecond=0)

    if appointment_date < today:
        return 'No puedes agendar citas en fechas pasadas.'

    if appointment_date == today and appointment_time <= current_time:
        return 'No puedes agendar citas en horarios que ya pasaron.'

    holiday = Holiday.objects.filter(date=appointment_date).first()
    if holiday:
        return (
            f'La fecha seleccionada es un día festivo ({holiday.name}) '
            'y no se pueden agendar citas.'
        )

    _, max_booking_date = _booking_date_limits()
    if appointment_date > max_booking_date:
        settings = SystemSettings.load()
        return (
            'Solo puedes agendar citas con hasta '
            f'{settings.max_advance_booking_days} días de anticipación.'
        )

    weekday = appointment_date.weekday()
    schedule = BuildingSchedule.objects.filter(
        building=building,
        day_of_week=weekday,
        is_active=True,
    ).first()
    if schedule is None:
        return 'Este edificio no tiene horario disponible para el día seleccionado.'

    if appointment_time < schedule.start_time or appointment_time > schedule.end_time:
        return (
            'La hora seleccionada está fuera del horario disponible '
            f'({schedule.start_time.strftime("%H:%M")} - '
            f'{schedule.end_time.strftime("%H:%M")}).'
        )

    active_appointments = Appointment.objects.filter(
        building=building,
        date=appointment_date,
        time=appointment_time,
        status=AppointmentStatus.ACTIVE,
    )
    if exclude_appointment_id:
        active_appointments = active_appointments.exclude(pk=exclude_appointment_id)

    if active_appointments.count() >= building.autos_por_turno:
        return 'Ya no hay espacios disponibles para esa fecha y hora.'

    return None


def get_available_time_slots(building, appointment_date, exclude_appointment_id=None):
    if not building.accepts_appointments:
        if not exclude_appointment_id:
            return []
        if not Appointment.objects.filter(
            pk=exclude_appointment_id,
            building=building,
        ).exists():
            return []

    if Holiday.objects.filter(date=appointment_date).exists():
        return []

    weekday = appointment_date.weekday()
    schedule = BuildingSchedule.objects.filter(
        building=building,
        day_of_week=weekday,
        is_active=True,
    ).first()
    if schedule is None:
        return []

    available = []
    for slot_time in _half_hour_slots(schedule.start_time, schedule.end_time):
        if (
            validate_appointment_slot(
                building,
                appointment_date,
                slot_time,
                exclude_appointment_id=exclude_appointment_id,
            )
            is None
        ):
            available.append(slot_time.strftime('%H:%M'))
    return available


def get_available_dates_in_month(
    building,
    year,
    month,
    exclude_appointment_id=None,
):
    _, last_day = calendar.monthrange(year, month)
    today, max_booking_date = _booking_date_limits()
    available_dates = []

    for day in range(1, last_day + 1):
        appointment_date = date(year, month, day)
        if appointment_date < today or appointment_date > max_booking_date:
            continue
        if get_available_time_slots(
            building,
            appointment_date,
            exclude_appointment_id=exclude_appointment_id,
        ):
            available_dates.append(appointment_date.isoformat())

    return available_dates
