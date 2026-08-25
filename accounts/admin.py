from django.contrib import admin

from .models import UserProfile, Vehicle


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_country_code', 'phone_number', 'car_plate')
    search_fields = ('user__username', 'user__email', 'phone_number', 'car_plate')


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('user', 'brand', 'model', 'plate', 'is_default')
    list_filter = ('is_default',)
    search_fields = ('user__username', 'user__email', 'brand', 'model', 'plate')
