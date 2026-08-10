from django.contrib import admin

from .models import MembershipPlan, MembershipSubscription


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'monthly_price',
        'monthly_wash_limit',
        'is_featured',
        'is_available_for_purchase',
        'is_active',
        'display_order',
    )
    list_filter = ('is_active', 'is_featured', 'is_available_for_purchase', 'accent')
    filter_horizontal = ('services',)
    search_fields = ('name', 'tier_label')


@admin.register(MembershipSubscription)
class MembershipSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'plan',
        'status',
        'current_period_start',
        'current_period_end',
        'created_at',
    )
    list_filter = ('status', 'plan')
    search_fields = ('user__username', 'user__email', 'plan__name')
    autocomplete_fields = ('user', 'plan')
