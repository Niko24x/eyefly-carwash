from django.urls import path

from . import views


urlpatterns = [
    path('precios/', views.service_pricing, name='service_pricing'),
    path('', views.service_list, name='service_list'),
    path('registrar/', views.service_create, name='service_create'),
    path('editar/<int:pk>/', views.service_update, name='service_update'),
]
