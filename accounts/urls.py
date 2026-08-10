from django.urls import path

from . import views


urlpatterns = [
    path('registro/', views.register, name='register'),
    path('mi-cuenta/', views.account_profile, name='account_profile'),
    path('mi-cuenta/editar/', views.account_profile_edit, name='account_profile_edit'),
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/registrar/', views.user_create, name='user_create'),
    path('usuarios/editar/<int:pk>/', views.user_update, name='user_update'),
]
