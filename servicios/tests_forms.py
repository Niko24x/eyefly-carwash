from decimal import Decimal

from django.test import TestCase

from .forms import ServiceForm
from .models import Service


class ServiceFormTests(TestCase):
    def _data(self, **overrides):
        data = {
            'name': 'Lavado completo',
            'description': 'Lavado exterior e interior.',
            'price': '150',
            'duration_minutes': 45,
            'badge': 'MÁS VENDIDO',
            'features': 'Aspirado\n!Encerado',
            'accent': 'red',
            'is_featured': True,
            'display_order': 2,
            'is_active': True,
        }
        data.update(overrides)
        return data

    def test_valid_service(self):
        form = ServiceForm(data=self._data())

        self.assertTrue(form.is_valid(), form.errors)
        service = form.save()
        self.assertEqual(service.name, 'Lavado completo')
        self.assertEqual(service.price, Decimal('150'))
        self.assertTrue(service.is_featured)

    def test_name_is_required(self):
        form = ServiceForm(data=self._data(name=''))

        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_rejects_invalid_accent(self):
        form = ServiceForm(data=self._data(accent='morado'))

        self.assertFalse(form.is_valid())
        self.assertIn('accent', form.errors)

    def test_rejects_non_numeric_price(self):
        form = ServiceForm(data=self._data(price='gratis'))

        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    def test_feature_items_parsing_marks_excluded(self):
        service = Service.objects.create(
            name='Plan',
            price=75,
            features='Incluido\n!No incluido',
        )

        items = service.feature_items()

        self.assertEqual(items[0], {'text': 'Incluido', 'included': True})
        self.assertEqual(items[1], {'text': 'No incluido', 'included': False})
