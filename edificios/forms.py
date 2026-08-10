from django import forms
from django.contrib.auth import get_user_model

from .models import Building


User = get_user_model()


class BuildingForm(forms.ModelForm):
    admins = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        label='Administradores',
        help_text='Selecciona usuarios registrados que podrán revisar las citas de este edificio.',
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['admins'].queryset = User.objects.filter(is_active=True).order_by(
            'username'
        )

    class Meta:
        model = Building
        fields = [
            'name',
            'address',
            'contact_name',
            'phone_number',
            'email',
            'image',
            'autos_por_turno',
            'admins',
            'notes',
        ]
        labels = {
            'name': 'Nombre del edificio',
            'address': 'Dirección',
            'contact_name': 'Persona de contacto',
            'phone_number': 'Número de teléfono',
            'email': 'Correo electrónico',
            'image': 'Imagen del edificio',
            'autos_por_turno': 'Autos por turno',
            'notes': 'Notas',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej. Torre Central'}),
            'address': forms.Textarea(
                attrs={'placeholder': 'Dirección completa del edificio', 'rows': 3}
            ),
            'contact_name': forms.TextInput(
                attrs={'placeholder': 'Nombre de la persona encargada'}
            ),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Ej. 5551234567'}),
            'email': forms.EmailInput(attrs={'placeholder': 'contacto@edificio.com'}),
            'autos_por_turno': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'notes': forms.Textarea(
                attrs={
                    'placeholder': 'Detalles útiles para coordinar el servicio',
                    'rows': 4,
                }
            ),
        }
