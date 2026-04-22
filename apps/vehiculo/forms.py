from django import forms
from .models import MarcaVehiculo, TipoVehiculo, Vehiculo

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', 'style': 'border-radius: 10px;'})

class NuevoVehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
            'propietario',
            'placa',
            'tipo',
            'marca',
            'modelo',
            'transporte',
            'chasis',
            'capacidad',
        ]

class MarcaVehiculoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MarcaVehiculo
        fields = ['nombre']


class TipoVehiculoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TipoVehiculo
        fields = ['tipo']

class VehiculoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['propietario',
                  'marca',
                  'modelo', 
                  'placa', 
                  'chasis', 
                  'capacidad']
        # widgets = {
        #     'marca': forms.Select(attrs={'class': 'form-select'}),
        #     'color': forms.Select(attrs={'class': 'form-select'}),
        #     'tipo_vehiculo': forms.Select(attrs={'class': 'form-select'}),
        #     'tipo_transporte': forms.Select(attrs={'class': 'form-select'}),
        #     'modelo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Año del vehículo (Ej. 2015)'}),
        #     'placa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 1234ABC'}),
        #     'chasis': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de chasis'}),
        #     'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número de pasajeros o toneladas'}),
        # }
