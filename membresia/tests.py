from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from appointments.models import Appointment
from edificios.models import Building
from membresia.models import MembershipPlan, MembershipSubscription, MembershipSubscriptionStatus
from membresia.services import find_membership_for_booking, remaining_washes
from servicios.models import Service

User = get_user_model()


class MembershipBookingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cliente',
            email='cliente@example.com',
            password='password123',
        )
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password123',
            is_staff=True,
        )
        self.building = Building.objects.create(
            created_by=self.staff,
            name='Torre Central',
            address='Av. Principal 123',
            contact_name='Ana Lopez',
            phone_number='5551234567',
            email='ana@example.com',
        )
        self.basico = Service.objects.create(name='Básico', price=75)
        self.completo = Service.objects.create(name='Completo', price=150)
        self.plan = MembershipPlan.objects.create(
            name='Silver',
            tier_label='Silver',
            monthly_price=249,
            monthly_wash_limit=2,
            display_order=1,
        )
        self.plan.services.add(self.basico)
        today = timezone.localdate()
        self.subscription = MembershipSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=MembershipSubscriptionStatus.ACTIVE,
            current_period_start=today.replace(day=1),
            current_period_end=today + timedelta(days=30),
        )

    def test_find_membership_when_credits_remain(self):
        subscription = find_membership_for_booking(self.user, self.basico)
        self.assertEqual(subscription, self.subscription)

    def test_membership_not_available_when_limit_reached(self):
        for index in range(2):
            Appointment.objects.create(
                user=self.user,
                building=self.building,
                service=self.basico,
                first_name='Ana',
                last_name='Lopez',
                phone_number='5551234567',
                email='ana@example.com',
                date=timezone.localdate() + timedelta(days=index + 1),
                time='10:00',
                membership_subscription=self.subscription,
                uses_membership=True,
            )

        self.assertIsNone(find_membership_for_booking(self.user, self.basico))
        self.assertEqual(remaining_washes(self.subscription, self.basico), 0)

    def test_membership_does_not_cover_unlisted_service(self):
        self.assertIsNone(find_membership_for_booking(self.user, self.completo))
