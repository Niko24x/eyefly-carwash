from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus

from .models import MembershipPlan, MembershipSubscription, MembershipSubscriptionStatus


def active_subscriptions_for_user(user, *, on_date=None):
    if not user or not user.is_authenticated:
        return MembershipSubscription.objects.none()

    on_date = on_date or timezone.localdate()
    return (
        MembershipSubscription.objects.filter(
            user=user,
            status=MembershipSubscriptionStatus.ACTIVE,
            current_period_start__lte=on_date,
            current_period_end__gte=on_date,
            plan__is_active=True,
        )
        .select_related('plan')
        .prefetch_related('plan__services')
    )


def _plan_covers_service(plan, service):
    if plan.covers_all_services:
        return True
    return plan.services.filter(pk=service.pk).exists()


def washes_used_in_period(subscription, *, service=None, exclude_appointment_id=None):
    queryset = Appointment.objects.filter(
        membership_subscription=subscription,
        status=AppointmentStatus.ACTIVE,
        uses_membership=True,
        date__gte=subscription.current_period_start,
        date__lte=subscription.current_period_end,
    )
    if service is not None:
        queryset = queryset.filter(service=service)
    if exclude_appointment_id:
        queryset = queryset.exclude(pk=exclude_appointment_id)
    return queryset.count()


def remaining_washes(subscription, service, *, exclude_appointment_id=None):
    plan = subscription.plan
    if not _plan_covers_service(plan, service):
        return 0

    if plan.monthly_wash_limit is None:
        return None

    used = washes_used_in_period(
        subscription,
        exclude_appointment_id=exclude_appointment_id,
    )
    return max(plan.monthly_wash_limit - used, 0)


def find_membership_for_booking(user, service, *, exclude_appointment_id=None):
    for subscription in active_subscriptions_for_user(user):
        remaining = remaining_washes(
            subscription,
            service,
            exclude_appointment_id=exclude_appointment_id,
        )
        if remaining is None or remaining > 0:
            return subscription
    return None


def membership_credit_summary(user):
    summary = []
    for subscription in active_subscriptions_for_user(user):
        plan = subscription.plan
        if plan.monthly_wash_limit is None:
            remaining_label = 'Ilimitados'
        else:
            used = washes_used_in_period(subscription)
            remaining = max(plan.monthly_wash_limit - used, 0)
            remaining_label = f'{remaining} de {plan.monthly_wash_limit}'

        service_ids = list(plan.services.values_list('pk', flat=True))
        summary.append(
            {
                'subscription_id': subscription.pk,
                'plan_name': plan.name,
                'remaining_label': remaining_label,
                'service_ids': service_ids,
                'covers_all_services': plan.covers_all_services,
            }
        )
    return summary
