import calendar
from datetime import date, timedelta

RECURRENCE_UNICA = 'unica'
RECURRENCE_SEMANAL = 'semanal'
RECURRENCE_QUINCENAL = 'quincenal'
RECURRENCE_MENSUAL = 'mensual'

RECURRENCE_CHOICES = [
    (RECURRENCE_UNICA, 'Solo esta vez'),
    (RECURRENCE_SEMANAL, 'Cada semana'),
    (RECURRENCE_QUINCENAL, 'Cada 15 días'),
    (RECURRENCE_MENSUAL, 'Cada mes'),
]

MAX_RECURRENCE_OCCURRENCES = 52


def generate_recurrence_dates(start_date, end_date, cadence):
    """Return occurrence dates from start through end for the given cadence.

    - unica: only the start date
    - semanal: same weekday every 7 days through end_date
    - quincenal: same weekday every 14 days through end_date
    - mensual: same calendar day each month; months without that day are skipped
    """
    if not isinstance(start_date, date):
        return []

    if cadence == RECURRENCE_UNICA or end_date is None:
        return [start_date]

    if end_date < start_date:
        return []

    if cadence == RECURRENCE_SEMANAL:
        dates = []
        current = start_date
        while current <= end_date and len(dates) < MAX_RECURRENCE_OCCURRENCES:
            dates.append(current)
            current += timedelta(days=7)
        return dates

    if cadence == RECURRENCE_QUINCENAL:
        dates = []
        current = start_date
        while current <= end_date and len(dates) < MAX_RECURRENCE_OCCURRENCES:
            dates.append(current)
            current += timedelta(days=14)
        return dates

    if cadence == RECURRENCE_MENSUAL:
        dates = []
        day = start_date.day
        year, month = start_date.year, start_date.month
        while len(dates) < MAX_RECURRENCE_OCCURRENCES:
            last_day = calendar.monthrange(year, month)[1]
            if day <= last_day:
                current = date(year, month, day)
                if current > end_date:
                    break
                if current >= start_date:
                    dates.append(current)

            if month == 12:
                year += 1
                month = 1
            else:
                month += 1

            if date(year, month, 1) > end_date:
                break
        return dates

    return [start_date]
