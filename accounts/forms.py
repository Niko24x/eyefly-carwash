from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .country_codes import DEFAULT_COUNTRY_CODE
from .phone_fields import (
    clean_phone_local_number,
    phone_country_code_field,
    phone_local_number_field,
)


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Email',
        widget=forms.TextInput(attrs={'placeholder': 'tu@email.com'}),
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'}),
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        if username and '@' in username:
            user = User.objects.filter(email__iexact=username).first()
            if user is not None:
                self.cleaned_data['username'] = user.get_username()
        return super().clean()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellido', max_length=150)
    email = forms.EmailField(label='Correo electrónico')
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        labels = {
            'username': 'Nombre de usuario',
        }


class ProfileEditForm(forms.Form):
    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellido', max_length=150)
    email = forms.EmailField(label='Correo electrónico')
    phone_country_code = phone_country_code_field(required=True)
    phone_local_number = phone_local_number_field(required=False)
    car_brand = forms.CharField(label='Marca del auto', max_length=80, required=False)
    car_model = forms.CharField(label='Modelo', max_length=80, required=False)
    car_color = forms.CharField(label='Color', max_length=40, required=False)
    car_plate = forms.CharField(label='Placa', max_length=20, required=False)
    parking_level = forms.CharField(label='Sótano', max_length=40, required=False)
    parking_number = forms.CharField(label='Número de parqueo', max_length=40, required=False)

    def __init__(self, *args, user=None, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
        if profile is not None:
            self.fields['phone_country_code'].initial = profile.phone_country_code
            self.fields['phone_local_number'].initial = profile.phone_number
            self.fields['car_brand'].initial = profile.car_brand
            self.fields['car_model'].initial = profile.car_model
            self.fields['car_color'].initial = profile.car_color
            self.fields['car_plate'].initial = profile.car_plate
            self.fields['parking_level'].initial = profile.parking_level
            self.fields['parking_number'].initial = profile.parking_number

    def clean_phone_local_number(self):
        country_code = self.cleaned_data.get('phone_country_code', DEFAULT_COUNTRY_CODE)
        return clean_phone_local_number(
            self.cleaned_data.get('phone_local_number', ''),
            country_code,
        )

    def save(self, user, profile):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save(update_fields=['first_name', 'last_name', 'email'])

        profile.phone_country_code = self.cleaned_data['phone_country_code']
        profile.phone_number = self.cleaned_data['phone_local_number']
        profile.car_brand = self.cleaned_data['car_brand']
        profile.car_model = self.cleaned_data['car_model']
        profile.car_color = self.cleaned_data['car_color']
        profile.car_plate = self.cleaned_data['car_plate']
        profile.parking_level = self.cleaned_data['parking_level']
        profile.parking_number = self.cleaned_data['parking_number']
        profile.save(
            update_fields=[
                'phone_country_code',
                'phone_number',
                'car_brand',
                'car_model',
                'car_color',
                'car_plate',
                'parking_level',
                'parking_number',
            ]
        )

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']
        labels = {
            'username': 'Nombre de usuario',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'is_active': 'Activo',
            'is_staff': 'Administrador',
        }


class StaffUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellido', max_length=150)
    email = forms.EmailField(label='Correo electrónico')
    is_active = forms.BooleanField(label='Activo', required=False, initial=True)
    is_staff = forms.BooleanField(label='Administrador', required=False)
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'is_active',
            'is_staff',
            'password1',
            'password2',
        ]
        labels = {
            'username': 'Nombre de usuario',
        }
