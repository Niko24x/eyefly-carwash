from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('citas/', views.appointment_list, name='appointment_list'),
    path('agendar/', views.appointment_create, name='appointment_create'),
    path('disponibilidad/', views.availability_api, name='availability_api'),
    path('editar/<int:pk>/', views.appointment_update, name='appointment_update'),
    path('reagendar/<int:pk>/', views.appointment_reschedule, name='appointment_reschedule'),
    path('cancelar/<int:pk>/', views.appointment_cancel, name='appointment_cancel'),
    path('calificar/<int:pk>/', views.appointment_review, name='appointment_review'),
    path('pago/<int:pk>/', views.appointment_payment, name='appointment_payment'),
]
