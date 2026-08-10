from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'first_name',
        'last_name',
        'user',
        'building',
        'service',
        'status',
        'is_paid',
        'payment_type',
        'rating',
        'phone_number',
        'email',
        'date',
        'time',
    )
    list_filter = ('building', 'service', 'status', 'is_paid', 'payment_type', 'rating', 'date')
    search_fields = (
        'first_name',
        'last_name',
        'phone_number',
        'email',
        'building__name',
        'service__name',
        'review_comment',
        'payment_reference',
    )

# Register your models here.
