from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from edificios.models import Building
from servicios.models import Service

from appointments.models import Appointment, AppointmentStatus

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea 3 citas pasadas de prueba para el usuario cliente (para calificar).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            default='cliente',
            help='Usuario dueño de las citas de prueba (default: cliente).',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        username = options['username']
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': 'Cliente',
                'last_name': 'Demo',
            },
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write(self.style.WARNING(
                f'Usuario "{username}" no existía; se creó con password123.'
            ))

        building = Building.objects.filter(accepts_appointments=True).order_by('id').first()
        if building is None:
            building = Building.objects.create(
                name='Torre Demo',
                address='Ciudad de Guatemala',
                contact_name='Demo',
                phone_number='55500000',
                email='demo@example.com',
                created_by=user,
                accepts_appointments=True,
            )
            self.stdout.write(self.style.WARNING('No había edificios; se creó Torre Demo.'))

        service = Service.objects.filter(is_active=True).order_by('id').first()
        if service is None:
            service = Service.objects.create(
                name='Lavado completo',
                description='Servicio de prueba.',
                is_active=True,
            )
            self.stdout.write(self.style.WARNING('No había servicios; se creó Lavado completo.'))

        today = timezone.localdate()
        samples = [
            {
                'days_ago': 3,
                'time': time(10, 0),
                'notes': 'Cita de prueba 1 — lista para calificar.',
            },
            {
                'days_ago': 7,
                'time': time(11, 30),
                'notes': 'Cita de prueba 2 — lista para calificar.',
            },
            {
                'days_ago': 14,
                'time': time(9, 0),
                'notes': 'Cita de prueba 3 — lista para calificar.',
            },
        ]

        created_count = 0
        for sample in samples:
            appointment_date = today - timedelta(days=sample['days_ago'])
            exists = Appointment.objects.filter(
                user=user,
                building=building,
                service=service,
                date=appointment_date,
                time=sample['time'],
                notes=sample['notes'],
            ).exists()
            if exists:
                continue

            Appointment.objects.create(
                user=user,
                building=building,
                service=service,
                first_name=user.first_name or 'Cliente',
                last_name=user.last_name or 'Demo',
                phone_number='50255512345',
                email=user.email or f'{username}@example.com',
                car_brand='Toyota',
                car_model='Corolla',
                car_color='Blanco',
                car_plate='P-TEST01',
                parking_level='S1',
                parking_number='A-10',
                notes=sample['notes'],
                date=appointment_date,
                time=sample['time'],
                status=AppointmentStatus.ACTIVE,
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {created_count} cita(s) pasada(s) para "{username}". '
            f'Total pasadas sin reseña: '
            f'{Appointment.objects.filter(user=user, rating__isnull=True, date__lt=today).count()}.'
        ))
