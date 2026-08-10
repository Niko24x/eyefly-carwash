from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from accounts.phone_utils import (
    clean_phone_for_country,
    combine_phone_number,
    format_local_phone_display,
    get_max_phone_length,
    split_phone_number,
)


class PhoneUtilsTests(SimpleTestCase):
    def test_get_max_phone_length_for_guatemala(self):
        self.assertEqual(get_max_phone_length('502'), 8)

    def test_get_max_phone_length_for_united_states(self):
        self.assertEqual(get_max_phone_length('1'), 10)

    def test_format_local_phone_display_for_eight_digits(self):
        self.assertEqual(format_local_phone_display('55512345', '502'), '5551-2345')

    def test_format_local_phone_display_for_nine_digits(self):
        self.assertEqual(format_local_phone_display('555123456', '51'), '555-123-456')

    def test_format_local_phone_display_for_ten_digits(self):
        self.assertEqual(format_local_phone_display('5551234567', '1'), '555-123-4567')

    def test_combine_and_split_phone_number(self):
        combined = combine_phone_number('502', '5551-2345')
        self.assertEqual(combined, '50255512345')

        country_code, local_number = split_phone_number(combined)
        self.assertEqual(country_code, '502')
        self.assertEqual(local_number, '55512345')

    def test_split_phone_number_without_country_code(self):
        country_code, local_number = split_phone_number('55512345')
        self.assertEqual(country_code, '502')
        self.assertEqual(local_number, '55512345')

    def test_clean_phone_for_country_rejects_too_many_digits(self):
        with self.assertRaises(ValidationError):
            clean_phone_for_country('555123456', '502')

    def test_clean_phone_for_country_accepts_valid_guatemala_number(self):
        self.assertEqual(clean_phone_for_country('5551-2345', '502'), '55512345')
