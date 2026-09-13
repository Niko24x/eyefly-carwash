from django.urls import path

from . import views


urlpatterns = [
    path('registro/', views.register, name='register'),
    path('mi-cuenta/', views.account_profile, name='account_profile'),
    path('mi-cuenta/editar/', views.account_profile_edit, name='account_profile_edit'),
    path('mi-cuenta/vehiculos/nuevo/', views.account_vehicle_create, name='account_vehicle_create'),
    path(
        'mi-cuenta/vehiculos/<int:pk>/editar/',
        views.account_vehicle_update,
        name='account_vehicle_update',
    ),
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/registrar/', views.user_create, name='user_create'),
    path('usuarios/editar/<int:pk>/', views.user_update, name='user_update'),
]
