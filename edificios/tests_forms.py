from django.contrib.auth import get_user_model
from django.test import TestCase

from .forms import BuildingForm
from .models import Building


User = get_user_model()


class BuildingFormTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='password123',
            is_staff=True,
        )
        self.admin_user = User.objects.create_user(
            username='encargado',
            email='encargado@example.com',
            password='password123',
        )

    def _data(self, **overrides):
        data = {
            'name': 'Torre Central',
            'address': 'Av. Principal 123',
            'contact_name': 'Ana Lopez',
            'phone_number': '5551234567',
            'email': 'ana@example.com',
            'autos_por_turno': 2,
            'admins': [self.admin_user.id],
            'notes': 'Entrada por estacionamiento.',
        }
        data.update(overrides)
        return data

    def test_valid_building(self):
        form = BuildingForm(data=self._data())

        self.assertTrue(form.is_valid(), form.errors)
        building = form.save(commit=False)
        building.created_by = self.creator
        building.save()
        form.save_m2m()
        self.assertIn(self.admin_user, building.admins.all())
        self.assertEqual(building.autos_por_turno, 2)

    def test_rejects_invalid_autos_por_turno(self):
        form = BuildingForm(data=self._data(autos_por_turno=0))

        self.assertFalse(form.is_valid())
        self.assertIn('autos_por_turno', form.errors)

    def test_name_is_required(self):
        form = BuildingForm(data=self._data(name=''))

        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_rejects_invalid_email(self):
        form = BuildingForm(data=self._data(email='no-es-correo'))

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_admins_are_optional(self):
        form = BuildingForm(data=self._data(admins=[]))

        self.assertTrue(form.is_valid(), form.errors)

    def test_inactive_user_cannot_be_admin(self):
        inactive = User.objects.create_user(
            username='inactivo',
            email='inactivo@example.com',
            password='password123',
            is_active=False,
        )
        form = BuildingForm(data=self._data(admins=[inactive.id]))

        self.assertFalse(form.is_valid())
        self.assertIn('admins', form.errors)
