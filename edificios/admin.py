from django.contrib import admin

from .models import Building


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'accepts_appointments',
        'autos_por_turno',
        'contact_name',
        'phone_number',
        'email',
        'created_by',
        'created_at',
    )
    list_filter = ('created_at', 'accepts_appointments')
    filter_horizontal = ('admins',)
    search_fields = (
        'name',
        'address',
        'contact_name',
        'phone_number',
        'email',
        'created_by__username',
        'admins__username',
    )
    readonly_fields = ('created_at', 'updated_at')
    fields = (
        'name',
        'address',
        'contact_name',
        'phone_number',
        'email',
        'image',
        'notes',
        'accepts_appointments',
        'autos_por_turno',
        'admins',
        'created_by',
        'created_at',
        'updated_at',
    )