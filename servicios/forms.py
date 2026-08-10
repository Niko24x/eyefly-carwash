from django import forms

from .models import Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            'name',
            'description',
            'price',
            'duration_minutes',
            'badge',
            'features',
            'accent',
            'is_featured',
            'display_order',
            'is_active',
        ]
        labels = {
            'name': 'Nombre del servicio',
            'description': 'Descripción',
            'price': 'Precio (Q)',
            'duration_minutes': 'Duración (minutos)',
            'badge': 'Etiqueta',
            'features': 'Características',
            'accent': 'Color de la tarjeta',
            'is_featured': 'Destacado',
            'display_order': 'Orden',
            'is_active': 'Activo',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ej. Lavado completo'}),
            'description': forms.Textarea(
                attrs={
                    'placeholder': 'Describe que incluye este servicio',
                    'rows': 4,
                }
            ),
            'badge': forms.TextInput(attrs={'placeholder': 'Ej. MÁS VENDIDO'}),
            'features': forms.Textarea(
                attrs={
                    'placeholder': (
                        'Una característica por línea.\n'
                        'Antepón ! para mostrarla como no incluida.'
                    ),
                    'rows': 6,
                }
            ),
            'is_active': forms.CheckboxInput(),
        }
