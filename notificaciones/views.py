from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import DeliveryChannel, DeliveryStatus, Notification
from .services import resend_notification_delivery


@staff_member_required
def notification_list(request):
    notifications = (
        Notification.objects.select_related(
            'appointment',
            'appointment__building',
            'appointment__service',
        )
        .prefetch_related('deliveries')
        .order_by('-created_at')
    )
    return render(
        request,
        'notificaciones/notification_list.html',
        {'notifications': notifications},
    )


@staff_member_required
@require_POST
def notification_resend_email(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    delivery = resend_notification_delivery(notification, DeliveryChannel.EMAIL)
    if delivery.status == DeliveryStatus.SENT:
        messages.success(request, 'La notificación por correo fue reenviada.')
    else:
        messages.error(
            request,
            'No se pudo reenviar el correo'
            + (f': {delivery.error_message}' if delivery.error_message else '.'),
        )
    return redirect('notification_list')


@staff_member_required
@require_POST
def notification_resend_whatsapp(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    resend_notification_delivery(notification, DeliveryChannel.WHATSAPP)
    messages.success(request, 'La notificación por WhatsApp fue encolada para reenvío.')
    return redirect('notification_list')
