from django.urls import path

from . import views


app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('descargas/usuarios/', views.download_users, name='download_users'),
    path('descargas/citas/', views.download_appointments, name='download_appointments'),
]
