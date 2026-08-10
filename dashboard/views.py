import calendar
import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus


User = get_user_model()


def _selected_month(request):
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        return date(year, month, 1)
    except (TypeError, ValueError):
        return today.replace(day=1)


def _month_bounds(month_start):
    if month_start.month == 12:
        return (
            month_start.replace(month=11),
            month_start.replace(year=month_start.year + 1, month=1),
        )

    if month_start.month == 1:
        previous_month = month_start.replace(year=month_start.year - 1, month=12)
    else:
        previous_month = month_start.replace(month=month_start.month - 1)

    next_month = month_start.replace(month=month_start.month + 1)
    return previous_month, next_month


def _calendar_weeks(month_start):
    month_appointments = Appointment.objects.select_related(
        'building',
        'service',
        'user',
    ).filter(
        date__year=month_start.year,
        date__month=month_start.month,
    )
    appointments_by_date = defaultdict(list)
    for appointment in month_appointments:
        appointments_by_date[appointment.date].append(appointment)

    weeks = []
    month_calendar = calendar.Calendar(firstweekday=0)
    for week in month_calendar.monthdatescalendar(month_start.year, month_start.month):
        weeks.append(
            [
                {
                    'date': day,
                    'in_month': day.month == month_start.month,
                    'is_today': day == timezone.localdate(),
                    'appointments': appointments_by_date.get(day, []),
                    'visible_appointments': appointments_by_date.get(day, [])[:2],
                    'hidden_appointments_count': max(
                        len(appointments_by_date.get(day, [])) - 2,
                        0,
                    ),
                }
                for day in week
            ]
        )
    return weeks


def _payment_summary():
    billable = Appointment.objects.filter(
        status=AppointmentStatus.ACTIVE,
        uses_membership=False,
    )

    paid_qs = billable.filter(is_paid=True)
    pending_qs = billable.filter(is_paid=False)

    paid_total = paid_qs.aggregate(
        total=Coalesce(Sum('service__price'), Decimal('0'))
    )['total']
    pending_total = pending_qs.aggregate(
        total=Coalesce(Sum('service__price'), Decimal('0'))
    )['total']

    return {
        'paid_count': paid_qs.count(),
        'pending_count': pending_qs.count(),
        'paid_total': paid_total,
        'pending_total': pending_total,
        'payment_total': paid_total + pending_total,
    }


@staff_member_required
def index(request):
    month_start = _selected_month(request)
    previous_month, next_month = _month_bounds(month_start)
    today = timezone.localdate()

    users = User.objects.annotate(appointment_count=Count('appointments')).order_by(
        '-date_joined'
    )
    appointments = Appointment.objects.select_related(
        'building',
        'service',
        'user',
    ).order_by(
        'date',
        'time',
    )
    payment_summary = _payment_summary()

    context = {
        'users': users,
        'appointments': appointments,
        'total_users': users.count(),
        'total_appointments': appointments.count(),
        'upcoming_appointments': appointments.filter(date__gte=today).count(),
        'today_appointments': appointments.filter(date=today).count(),
        'calendar_weeks': _calendar_weeks(month_start),
        'month_start': month_start,
        'previous_month': previous_month,
        'next_month': next_month,
        'weekdays': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
        **payment_summary,
    }
    return render(request, 'dashboard/index.html', context)


@staff_member_required
def download_users(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usuarios.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            'id',
            'usuario',
            'nombre',
            'apellido',
            'correo',
            'staff',
            'activo',
            'fecha_registro',
        ]
    )
    for user in User.objects.order_by('id'):
        writer.writerow(
            [
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                user.email,
                user.is_staff,
                user.is_active,
                user.date_joined.isoformat(),
            ]
        )

    return response


@staff_member_required
def download_appointments(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="citas.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            'id',
            'usuario',
            'edificio',
            'nombre',
            'apellido',
            'teléfono',
            'correo',
            'fecha',
            'hora',
            'pagada',
            'tipo_pago',
            'referencia',
            'fecha_creación',
        ]
    )
    appointments = Appointment.objects.select_related(
        'building',
        'service',
        'user',
    ).order_by(
        'date',
        'time',
    )
    for appointment in appointments:
        writer.writerow(
            [
                appointment.id,
                appointment.user.username,
                appointment.building.name,
                appointment.first_name,
                appointment.last_name,
                appointment.phone_number,
                appointment.email,
                appointment.date.isoformat(),
                appointment.time.strftime('%H:%M'),
                appointment.is_paid,
                appointment.payment_type,
                appointment.payment_reference,
                appointment.created_at.isoformat(),
            ]
        )

    return response
