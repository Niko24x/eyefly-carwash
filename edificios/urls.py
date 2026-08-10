from django.urls import path

from . import views


urlpatterns = [
    path('', views.building_list, name='building_list'),
    path('registrar/', views.building_create, name='building_create'),
    path('editar/<int:pk>/', views.building_update, name='building_update'),
    path(
        'alternar-citas/<int:pk>/',
        views.building_toggle_appointments,
        name='building_toggle_appointments',
    ),
]
