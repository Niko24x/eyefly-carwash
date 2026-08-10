from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import BuildingForm
from .models import Building


@staff_member_required
def building_list(request):
    buildings = Building.objects.all().order_by('-created_at')
    return render(
        request,
        'edificios/building_list.html',
        {'buildings': buildings},
    )


@staff_member_required
def building_create(request):
    if request.method == 'POST':
        form = BuildingForm(request.POST, request.FILES)
        if form.is_valid():
            building = form.save(commit=False)
            building.created_by = request.user
            building.save()
            form.save_m2m()
            building.admins.add(request.user)
            messages.success(request, 'Tu edificio fue registrado correctamente.')
            return redirect('building_list')
    else:
        form = BuildingForm()

    return render(
        request,
        'edificios/building_form.html',
        {
            'form': form,
            'page_title': 'Registrar edificio',
            'page_description': (
                'Comparte los datos del edificio para evaluar y coordinar el servicio.'
            ),
            'submit_label': 'Guardar edificio',
        },
    )


@staff_member_required
def building_update(request, pk):
    building = get_object_or_404(Building, pk=pk)
    if request.method == 'POST':
        form = BuildingForm(request.POST, request.FILES, instance=building)
        if form.is_valid():
            form.save()
            messages.success(request, 'El edificio fue actualizado correctamente.')
            return redirect('building_list')
    else:
        form = BuildingForm(instance=building)

    return render(
        request,
        'edificios/building_form.html',
        {
            'form': form,
            'building': building,
            'page_title': 'Editar edificio',
            'page_description': 'Actualiza los datos del edificio seleccionado.',
            'submit_label': 'Guardar cambios',
        },
    )


@staff_member_required
@require_POST
def building_toggle_appointments(request, pk):
    building = get_object_or_404(Building, pk=pk)
    building.accepts_appointments = not building.accepts_appointments
    building.save(update_fields=['accepts_appointments', 'updated_at'])

    if building.accepts_appointments:
        messages.success(
            request,
            f'{building.name} vuelve a aceptar nuevas citas.',
        )
    else:
        messages.success(
            request,
            f'{building.name} ya no acepta nuevas citas.',
        )

    return redirect('building_list')
