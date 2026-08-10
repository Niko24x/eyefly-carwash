from django.contrib import admin

from .models import BuildingSchedule, Holiday, SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'name')
    ordering = ('date',)


@admin.register(BuildingSchedule)
class BuildingScheduleAdmin(admin.ModelAdmin):
    list_display = ('building', 'day_of_week', 'start_time', 'end_time', 'is_active')
    list_filter = ('building', 'is_active')
