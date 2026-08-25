from datetime import date, datetime, time, timedelta
import calendar
from zoneinfo import ZoneInfo

from django.utils import timezone
from appointments.models import Appointment, AppointmentStatus
from configuracion.models import BuildingSchedule, Holiday, SystemSettings


def _time_slots(start_time, end_time, interval_minutes):
    slots = []
    current = datetime.combine(date.today(), start_time)
    while current.time() <= end_time:
        slot_time = current.time().replace(second=0, microsecond=0)
        slots.append(slot_time)
        current += timedelta(minutes=interval_minutes)
    return slots


def slot_interval_minutes():
    return SystemSettings.load().slot_interval_minutes


def _booking_date_limits():
    settings = SystemSettings.load()
    today = timezone.localdate()
    max_date = today + timedelta(days=settings.max_advance_booking_days)
    return today, max_date


def _local_now():
    return timezone.localtime()


def _service_duration(service):
    if service is None:
        return 30
    return service.duration_minutes or 30


def _appointment_interval(appointment):
    start = datetime.combine(appointment.date, appointment.time)
    end = start + timedelta(minutes=_service_duration(appointment.service))
    return start, end


def _candidate_interval(appointment_date, appointment_time, service):
    start = datetime.combine(appointment_date, appointment_time)
    end = start + timedelta(minutes=_service_duration(service))
    return start, end


def validate_appointment_slot(
    building,
    appointment_date,
    appointment_time,
    service=None,
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

    candidate_start, candidate_end = _candidate_interval(
        appointment_date,
        appointment_time,
        service,
    )
    schedule_start = datetime.combine(appointment_date, schedule.start_time)
    schedule_end = datetime.combine(appointment_date, schedule.end_time)

    if candidate_start < schedule_start or candidate_end > schedule_end:
        return (
            'La hora seleccionada está fuera del horario disponible '
            f'({schedule.start_time.strftime("%H:%M")} - '
            f'{schedule.end_time.strftime("%H:%M")}).'
        )

    active_appointments = Appointment.objects.filter(
        building=building,
        date=appointment_date,
        status=AppointmentStatus.ACTIVE,
    ).select_related('service')
    if exclude_appointment_id:
        active_appointments = active_appointments.exclude(pk=exclude_appointment_id)

    overlapping = []
    check_points = {candidate_start}
    for appointment in active_appointments:
        existing_start, existing_end = _appointment_interval(appointment)
        if existing_start < candidate_end and candidate_start < existing_end:
            overlapping.append((existing_start, existing_end))
            if candidate_start <= existing_start < candidate_end:
                check_points.add(existing_start)

    for check_point in check_points:
        concurrent = sum(
            1
            for existing_start, existing_end in overlapping
            if existing_start <= check_point < existing_end
        )
        if concurrent >= building.autos_por_turno:
            return 'Ya no hay espacios disponibles para esa fecha y hora.'

    return None


def get_available_time_slots(
    building,
    appointment_date,
    exclude_appointment_id=None,
    service=None,
):
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
    for slot_time in _time_slots(
        schedule.start_time,
        schedule.end_time,
        slot_interval_minutes(),
    ):
        if (
            validate_appointment_slot(
                building,
                appointment_date,
                slot_time,
                service=service,
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
    service=None,
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
            service=service,
        ):
            available_dates.append(appointment_date.isoformat())
    return available_dates
