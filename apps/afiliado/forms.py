from django import forms
from .models import Afiliado

class NuevoAfiliadoForm(forms.ModelForm):
    class Meta:
        model = Afiliado
        fields = ['nombre_completo']
        labels = {
            'nombre_completo': 'Nombre Completo',
        }
        widgets = {
            'nombre_completo': forms.TextInput(
                attrs={
                    'list': 'lista_afiliados',
                    'autocomplete': 'off',
                    'placeholder': 'Ej. Juan Pérez...',
                }
            ),
        }

class EditarAfiliadoForm(forms.ModelForm):
    class Meta:
        model = Afiliado
        fields = ['operador', 'nombre_completo']
        labels = {
            'operador': 'Empresa Operadora / Organización',
            'nombre_completo': 'Nombre Completo',
        }
        widgets = {
            'operador': forms.Select(
                attrs={
                    'class': 'form-select',
                }
            ),
            'nombre_completo': forms.TextInput(
                attrs={
                    'autocomplete': 'off',
                    'placeholder': 'Ej. Juan Pérez...',
                }
            ),
        }