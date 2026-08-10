from django.contrib import admin

from .models import Notification, NotificationDelivery


class NotificationDeliveryInline(admin.TabularInline):
    model = NotificationDelivery
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'sent_at')
    fields = (
        'channel',
        'destination',
        'status',
        'sent_at',
        'error_message',
        'created_at',
        'updated_at',
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'event_type', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = (
        'message',
        'appointment__first_name',
        'appointment__last_name',
        'appointment__email',
        'appointment__phone_number',
    )
    readonly_fields = ('created_at',)
    inlines = [NotificationDeliveryInline]


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        'notification',
        'channel',
        'destination',
        'status',
        'sent_at',
        'updated_at',
    )
    list_filter = ('channel', 'status', 'sent_at')
    search_fields = ('destination', 'error_message', 'notification__message')
    readonly_fields = ('created_at', 'updated_at')
