from django.urls import path

from . import views


app_name = 'configuracion'


urlpatterns = [
    path('', views.settings_index, name='index'),
    path('general/', views.general_settings, name='general_settings'),
    path('festivos/', views.holiday_list, name='holiday_list'),
    path('festivos/eliminar/<int:pk>/', views.holiday_delete, name='holiday_delete'),
    path('horarios/', views.building_schedule_list, name='building_schedule_list'),
    path(
        'horarios/<int:pk>/',
        views.building_schedule_edit,
        name='building_schedule_edit',
    ),
]
