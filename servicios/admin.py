from django.contrib import admin

from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'price',
        'duration_minutes',
        'accent',
        'is_featured',
        'display_order',
        'is_active',
    )
    list_filter = ('is_active', 'is_featured', 'accent', 'created_at')
    list_editable = ('display_order', 'is_featured', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
