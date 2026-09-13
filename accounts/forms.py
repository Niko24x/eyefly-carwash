from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .country_codes import DEFAULT_COUNTRY_CODE
from .models import Vehicle
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

    def __init__(self, *args, user=None, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
        if profile is not None:
            self.fields['phone_country_code'].initial = profile.phone_country_code
            self.fields['phone_local_number'].initial = profile.phone_number

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
        profile.save(update_fields=['phone_country_code', 'phone_number'])


def sync_profile_from_vehicle(user, vehicle):
    from .models import UserProfile

    profile, _created = UserProfile.objects.get_or_create(user=user)
    profile.car_brand = vehicle.brand
    profile.car_model = vehicle.model
    profile.car_color = vehicle.color
    profile.car_plate = vehicle.plate
    profile.parking_level = vehicle.parking_level
    profile.parking_number = vehicle.parking_number
    profile.save(
        update_fields=[
            'car_brand',
            'car_model',
            'car_color',
            'car_plate',
            'parking_level',
            'parking_number',
        ]
    )


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'brand',
            'model',
            'color',
            'plate',
            'parking_level',
            'parking_number',
            'is_default',
        ]
        labels = {
            'brand': 'Marca del auto',
            'model': 'Modelo',
            'color': 'Color',
            'plate': 'Placa',
            'parking_level': 'Sótano',
            'parking_number': 'Número de parqueo',
            'is_default': 'Usar como predeterminado',
        }
        widgets = {
            'brand': forms.TextInput(attrs={'placeholder': 'Toyota'}),
            'model': forms.TextInput(attrs={'placeholder': 'Raize'}),
            'color': forms.TextInput(attrs={'placeholder': 'Rojo'}),
            'plate': forms.TextInput(attrs={'placeholder': '753KIJ'}),
            'parking_level': forms.TextInput(attrs={'placeholder': 'S1'}),
            'parking_number': forms.TextInput(attrs={'placeholder': '12'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.vehicle_user = user
        super().__init__(*args, **kwargs)
        self.fields['is_default'].required = False
        if self.instance.pk is None and user is not None:
            self.fields['is_default'].initial = not user.vehicles.exists()

    def clean_plate(self):
        plate = (self.cleaned_data.get('plate') or '').strip()
        user = self.vehicle_user
        if user is None:
            return plate
        duplicates = Vehicle.objects.filter(user=user, plate__iexact=plate)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError('Ya tienes un vehículo con esa placa.')
        return plate

    def save(self, user=None, commit=True):
        user = user or self.vehicle_user
        vehicle = super().save(commit=False)
        vehicle.user = user
        make_default = bool(self.cleaned_data.get('is_default'))
        if user and (make_default or not user.vehicles.exclude(pk=vehicle.pk or 0).exists()):
            vehicle.is_default = True
        if commit:
            if vehicle.is_default:
                Vehicle.objects.filter(user=user).exclude(pk=vehicle.pk or 0).update(
                    is_default=False
                )
            vehicle.save()
            if vehicle.is_default:
                sync_profile_from_vehicle(user, vehicle)
        return vehicle


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
