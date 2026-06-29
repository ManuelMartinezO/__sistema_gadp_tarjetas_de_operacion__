from django import forms
from .models import MarcaVehiculo, TipoVehiculo, Vehiculo

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.update({
                'class': widget_class, 
                'style': 'border-radius: 10px;'
            })

class NuevoVehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
            'propietario', 'placa', 'tipo', 'marca', 
            'modelo', 'transporte', 'chasis', 'capacidad'
        ]
        labels = {
            'propietario': 'Nombre del Propietario',
            'placa': 'Número de Placa',
            'tipo': 'Tipo de Vehículo',
            'marca': 'Marca',
            'modelo': 'Modelo (Año)',
            'transporte': 'Tipo de Transporte',
            'chasis': 'Número de Chasis (VIN)',
            'capacidad': 'Capacidad',
        }
        widgets = {
            'propietario': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo del propietario...', 'id': 'input-vehiculo-propietario'}),
            'placa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 1234ABC', 'style': 'text-transform: uppercase; border-radius: 10px;', 'id': 'input-vehiculo-placa'}),
            'modelo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 2015', 'id': 'input-vehiculo-modelo'}),
            'chasis': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el número de chasis...', 'id': 'input-vehiculo-chasis'}),
            'capacidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 45', 'id': 'input-vehiculo-capacidad'}),

            'tipo': forms.Select(attrs={'class': 'form-control', 'id': 'input-vehiculo-tipo'}),
            'marca': forms.Select(attrs={'class': 'form-control', 'id': 'input-vehiculo-marca'}),
            'transporte': forms.Select(attrs={'class': 'form-control', 'id': 'input-vehiculo-transporte'}),
        }

class EditarVehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
            'afiliado', 'propietario', 'placa', 'tipo', 
            'marca', 'modelo', 'transporte', 'chasis', 'capacidad'
        ]
        labels = {
            'afiliado': 'Afiliado Vinculado',
            'propietario': 'Nombre del Propietario',
            'placa': 'Número de Placa',
            'tipo': 'Tipo de Vehículo',
            'marca': 'Marca',
            'modelo': 'Modelo (Año)',
            'transporte': 'Tipo de Transporte',
            'chasis': 'Número de Chasis (VIN)',
            'capacidad': 'Capacidad',
        }
        widgets = {
            'propietario': forms.TextInput(attrs={'placeholder': 'Nombre completo del propietario...'}),
            'placa': forms.TextInput(attrs={'placeholder': 'Ej. 1234ABC', 'style': 'text-transform: uppercase; border-radius: 10px;'}),
            'modelo': forms.NumberInput(attrs={'placeholder': 'Ej. 2015'}),
            'chasis': forms.TextInput(attrs={'placeholder': 'Ingrese el número de chasis...'}),
            'capacidad': forms.NumberInput(attrs={'placeholder': 'Ej. 45'}),
        }

class MarcaVehiculoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MarcaVehiculo
        fields = ['nombre']
        labels = {
            'nombre': 'Nombre de la Marca'
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Toyota, Nissan, Volvo...'})
        }

class TipoVehiculoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TipoVehiculo
        fields = ['tipo']
        labels = {
            'tipo': 'Tipo de Vehículo'
        }
        widgets = {
            'tipo': forms.TextInput(attrs={'placeholder': 'Ej. Minibus, Taxi, Vagoneta...'})
        }