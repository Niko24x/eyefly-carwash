from django import forms

from .country_codes import COUNTRY_CODE_CHOICES, DEFAULT_COUNTRY_CODE
from .phone_utils import clean_phone_for_country, get_max_phone_length, phone_placeholder_for_length


class PhoneCountryCodeSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs,
        )
        if value:
            option['attrs']['data-max-digits'] = str(get_max_phone_length(value))
        return option


PHONE_COUNTRY_CODE_WIDGET = PhoneCountryCodeSelect(
    attrs={'class': 'phone-country-code-select', 'aria-label': 'Código de país'},
)

PHONE_LOCAL_NUMBER_WIDGET = forms.TextInput(
    attrs={
        'class': 'phone-local-number-input',
        'inputmode': 'tel',
        'autocomplete': 'tel-national',
        'placeholder': phone_placeholder_for_length(get_max_phone_length(DEFAULT_COUNTRY_CODE)),
        'aria-label': 'Número de teléfono',
    },
)


def phone_country_code_field(required=True):
    return forms.ChoiceField(
        label='Código de país',
        choices=COUNTRY_CODE_CHOICES,
        initial=DEFAULT_COUNTRY_CODE,
        required=required,
        widget=PHONE_COUNTRY_CODE_WIDGET,
    )


def phone_local_number_field(required=True):
    return forms.CharField(
        label='Número de teléfono',
        max_length=16,
        required=required,
        widget=PHONE_LOCAL_NUMBER_WIDGET,
    )


def clean_phone_local_number(value, country_code=DEFAULT_COUNTRY_CODE):
    return clean_phone_for_country(value, country_code)
