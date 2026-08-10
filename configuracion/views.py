from datetime import time

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

from edificios.models import Building

from .forms import BuildingScheduleFormSet, HolidayForm, SystemSettingsForm
from .models import BuildingSchedule, Holiday, SystemSettings


def _ensure_building_schedules(building):
    for day in range(7):
        BuildingSchedule.objects.get_or_create(
            building=building,
            day_of_week=day,
            defaults={
                'start_time': time(9, 0),
                'end_time': time(17, 0),
                'is_active': day < 5,
            },
        )


@staff_member_required
def settings_index(request):
    return render(request, 'configuracion/index.html')


@staff_member_required
def general_settings(request):
    settings = SystemSettings.load()
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'La configuración general fue actualizada.')
            return redirect('configuracion:general_settings')
    else:
        form = SystemSettingsForm(instance=settings)

    return render(
        request,
        'configuracion/general_settings.html',
        {'form': form},
    )


@staff_member_required
def holiday_list(request):
    holidays = Holiday.objects.all()
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'El día festivo fue registrado correctamente.')
            return redirect('configuracion:holiday_list')
    else:
        form = HolidayForm()

    return render(
        request,
        'configuracion/holiday_list.html',
        {
            'holidays': holidays,
            'form': form,
        },
    )


@staff_member_required
def holiday_delete(request, pk):
    holiday = get_object_or_404(Holiday, pk=pk)
    if request.method == 'POST':
        holiday.delete()
        messages.success(request, 'El día festivo fue eliminado correctamente.')
        return redirect('configuracion:holiday_list')

    return render(
        request,
        'configuracion/holiday_delete.html',
        {'holiday': holiday},
    )


@staff_member_required
def building_schedule_list(request):
    buildings = Building.objects.all().order_by('name')
    return render(
        request,
        'configuracion/building_schedule_list.html',
        {'buildings': buildings},
    )


@staff_member_required
def building_schedule_edit(request, pk):
    building = get_object_or_404(Building, pk=pk)
    _ensure_building_schedules(building)

    if request.method == 'POST':
        formset = BuildingScheduleFormSet(
            request.POST,
            instance=building,
        )
        if formset.is_valid():
            formset.save()
            messages.success(
                request,
                f'El horario de {building.name} fue actualizado correctamente.',
            )
            return redirect('configuracion:building_schedule_list')
    else:
        formset = BuildingScheduleFormSet(instance=building)

    weekday_labels = dict(BuildingSchedule.Weekday.choices)
    schedule_forms = [
        (weekday_labels[form.instance.day_of_week], form)
        for form in formset.forms
    ]

    return render(
        request,
        'configuracion/building_schedule_form.html',
        {
            'building': building,
            'formset': formset,
            'schedule_forms': schedule_forms,
        },
    )
