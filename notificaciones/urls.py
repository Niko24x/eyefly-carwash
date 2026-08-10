from django.urls import path

from . import views


urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path(
        '<int:pk>/reenviar-correo/',
        views.notification_resend_email,
        name='notification_resend_email',
    ),
    path(
        '<int:pk>/reenviar-whatsapp/',
        views.notification_resend_whatsapp,
        name='notification_resend_whatsapp',
    ),
]
