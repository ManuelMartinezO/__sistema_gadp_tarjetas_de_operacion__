from django import forms
from .models import Operador, Organizacion, Federacion

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.update({
                'class': widget_class, 
                'style': 'border-radius: 10px;'
            })

class NuevoOperadorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Operador
        fields = ['organizacion', 'federacion']
        labels = {
            'organizacion': 'Organización a la que pertenece',
            'federacion': 'Federación asociada',
        }

class OrganizacionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Organizacion
        fields = ['nombre']
        labels = {
            'nombre': 'Nombre de la Organización',
        }
        widgets = {
            'nombre': forms.TextInput(
                attrs={'placeholder': 'Ej. Sindicato 1ro de Mayo, Cooperativa San Cristóbal...'}
            ),
        }

class FederacionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Federacion
        fields = ['nombre']
        labels = {
            'nombre': 'Nombre de la Federación',
        }
        widgets = {
            'nombre': forms.TextInput(
                attrs={'placeholder': 'Ej. Fed. Departamental de Choferes 16 de Noviembre...'}
            ),
        }