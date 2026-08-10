import re

from django.core.exceptions import ValidationError

from .country_codes import (
    COUNTRY_CODE_CHOICES,
    COUNTRY_PHONE_LENGTHS,
    DEFAULT_COUNTRY_CODE,
    DEFAULT_PHONE_LENGTH,
)

COUNTRY_CODES = [code for code, _ in COUNTRY_CODE_CHOICES]


def digits_only(value):
    return re.sub(r'\D', '', value or '')


def get_max_phone_length(country_code):
    return COUNTRY_PHONE_LENGTHS.get(country_code, DEFAULT_PHONE_LENGTH)


def phone_placeholder_for_length(max_length):
    samples = {
        7: '622-1234',
        8: '5555-1234',
        9: '555-123-456',
        10: '555-123-4567',
        11: '11-98765-4321',
    }
    return samples.get(max_length, '5555-1234')


def combine_phone_number(country_code, local_number):
    local = digits_only(local_number)
    if not local:
        return ''
    return f'{country_code}{local}'


def split_phone_number(phone_number, default_code=DEFAULT_COUNTRY_CODE):
    digits = digits_only(phone_number)
    if not digits:
        return default_code, ''

    default_max = get_max_phone_length(default_code)
    if len(digits) <= default_max:
        return default_code, digits

    for code in sorted(COUNTRY_CODES, key=len, reverse=True):
        if not digits.startswith(code) or len(digits) <= len(code):
            continue

        local = digits[len(code):]
        max_local = get_max_phone_length(code)
        min_local = max(7, max_local - 2)

        if len(local) <= max_local and len(local) >= min_local:
            return code, local

    return default_code, digits


def format_local_phone_display(local_digits, country_code=None):
    digits = digits_only(local_digits)
    if not digits:
        return ''

    max_length = get_max_phone_length(country_code) if country_code else len(digits)
    digits = digits[:max_length]
    length = len(digits)

    if max_length <= 8:
        if length <= 4:
            return digits
        return f'{digits[:4]}-{digits[4:]}'

    if max_length == 9:
        if length <= 3:
            return digits
        if length <= 6:
            return f'{digits[:3]}-{digits[3:]}'
        return f'{digits[:3]}-{digits[3:6]}-{digits[6:]}'

    if max_length == 10:
        if length <= 3:
            return digits
        if length <= 6:
            return f'{digits[:3]}-{digits[3:]}'
        return f'{digits[:3]}-{digits[3:6]}-{digits[6:]}'

    if max_length >= 11:
        if length <= 2:
            return digits
        if length <= 7:
            return f'{digits[:2]}-{digits[2:]}'
        return f'{digits[:2]}-{digits[2:7]}-{digits[7:]}'

    return digits


def clean_phone_for_country(value, country_code):
    local = digits_only(value)
    max_length = get_max_phone_length(country_code)
    if len(local) > max_length:
        raise ValidationError(
            f'El número no puede tener más de {max_length} dígitos para este país.'
        )
    return local
