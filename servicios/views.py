from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ServiceForm
from .models import Service

from membresia.models import MembershipPlan


SERVICE_FAQ = [
    {
        'question': '¿Cuánto tarda el servicio?',
        'answer': (
            'El Básico tarda aproximadamente 30 minutos, el Completo 45 minutos y el '
            'Premium Detail hasta 90 minutos. Todo depende del estado del vehículo.'
        ),
    },
    {
        'question': '¿Necesito estar presente?',
        'answer': (
            'No necesitas estar presente. Solo deja tu vehículo en el parqueo designado '
            'del edificio. Recibirás una notificación cuando esté listo.'
        ),
    },
    {
        'question': '¿Qué métodos de pago aceptan?',
        'answer': (
            'Aceptamos tarjetas de crédito y débito (Visa, Mastercard, Amex) a través '
            'de Stripe. Pago 100% seguro y encriptado.'
        ),
    },
    {
        'question': '¿Puedo cancelar mi reserva?',
        'answer': (
            'Sí, puedes cancelar tu reserva hasta 24 horas antes de la cita sin costo. '
            'Cancelaciones con menos de 24 horas pueden tener un cargo del 50%.'
        ),
    },
]


def service_pricing(request):
    services = Service.objects.filter(is_active=True).order_by('display_order', 'name')
    membership_plans = MembershipPlan.objects.filter(is_active=True).order_by('display_order', 'name')
    return render(
        request,
        'servicios/service_pricing.html',
        {
            'services': services,
            'membership_plans': membership_plans,
            'service_faq': SERVICE_FAQ,
        },
    )


@staff_member_required
def service_list(request):
    services = Service.objects.all()
    return render(
        request,
        'servicios/service_list.html',
        {'services': services},
    )


@staff_member_required
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'El servicio fue registrado correctamente.')
            return redirect('service_list')
    else:
        form = ServiceForm()

    return render(
        request,
        'servicios/service_form.html',
        {
            'form': form,
            'page_title': 'Registrar servicio',
            'page_description': (
                'Define un servicio que los clientes podrán solicitar al agendar una cita.'
            ),
            'submit_label': 'Guardar servicio',
        },
    )


@staff_member_required
def service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'El servicio fue actualizado correctamente.')
            return redirect('service_list')
    else:
        form = ServiceForm(instance=service)

    return render(
        request,
        'servicios/service_form.html',
        {
            'form': form,
            'service': service,
            'page_title': 'Editar servicio',
            'page_description': 'Actualiza los datos del servicio seleccionado.',
            'submit_label': 'Guardar cambios',
        },
    )
