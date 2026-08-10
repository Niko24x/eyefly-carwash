from datetime import time

from django.test import TestCase

from .forms import BuildingScheduleDayForm, HolidayForm, SystemSettingsForm


class SystemSettingsFormTests(TestCase):
    def test_valid_settings(self):
        form = SystemSettingsForm(
            data={
                'max_concurrent_appointments': 3,
                'max_advance_booking_days': 30,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_negative_values(self):
        form = SystemSettingsForm(
            data={
                'max_concurrent_appointments': -1,
                'max_advance_booking_days': 30,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('max_concurrent_appointments', form.errors)

    def test_requires_fields(self):
        form = SystemSettingsForm(data={})

        self.assertFalse(form.is_valid())
        self.assertIn('max_concurrent_appointments', form.errors)
        self.assertIn('max_advance_booking_days', form.errors)


class HolidayFormTests(TestCase):
    def test_valid_holiday(self):
        form = HolidayForm(data={'date': '2026-12-25', 'name': 'Navidad'})

        self.assertTrue(form.is_valid(), form.errors)

    def test_requires_date(self):
        form = HolidayForm(data={'date': '', 'name': 'Navidad'})

        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_rejects_invalid_date(self):
        form = HolidayForm(data={'date': 'no-es-fecha', 'name': 'Navidad'})

        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)


class BuildingScheduleDayFormTests(TestCase):
    def _data(self, **overrides):
        data = {
            'day_of_week': 0,
            'is_active': True,
            'start_time': '08:00',
            'end_time': '18:00',
        }
        data.update(overrides)
        return data

    def test_valid_active_schedule(self):
        form = BuildingScheduleDayForm(data=self._data())

        self.assertTrue(form.is_valid(), form.errors)

    def test_rejects_start_after_end_when_active(self):
        form = BuildingScheduleDayForm(
            data=self._data(start_time='18:00', end_time='08:00')
        )

        self.assertFalse(form.is_valid())
        self.assertIn('anterior a la hora de fin', str(form.errors))

    def test_allows_invalid_range_when_inactive(self):
        form = BuildingScheduleDayForm(
            data=self._data(is_active=False, start_time='18:00', end_time='08:00')
        )

        self.assertTrue(form.is_valid(), form.errors)
