from django import forms
from .models import Tramite, Deposito

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                widget_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
                field.widget.attrs.update({
                    'class': widget_class,
                    'style': 'border-radius: 10px;'
                })

class NuevoTramiteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tramite
        fields = ['usuario', 'operador', 'tipo', 'licencia', 'fojas', 'rutas']
        labels = {
            'usuario': 'Usuario Responsable',
            'operador': 'Empresa Operadora',
            'tipo': 'Tipo de Trámite',
            'licencia': 'Número de Licencia',
            'fojas': 'Cantidad de Fojas',
            'rutas': 'Rutas Solicitadas',
        }
        widgets = {
            'licencia': forms.TextInput(attrs={'placeholder': 'Ej. 12345-A'}),
            'fojas': forms.NumberInput(attrs={'placeholder': 'Ej. 15'}),
            'rutas': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Detalle de rutas solicitadas...'}),
        }

class EditarTramiteAdminForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tramite
        fields = ['tipo', 'estado', 'licencia', 'usuario', 'operador', 'fojas', 'rutas', 'observacion']
        labels = {
            'tipo': 'Tipo de Trámite',
            'estado': 'Estado del Trámite',
            'licencia': 'Número de Licencia',
            'usuario': 'Usuario Asignado',
            'operador': 'Empresa Operadora',
            'fojas': 'Cantidad de Fojas',
            'rutas': 'Rutas Aprobadas/Solicitadas',
            'observacion': 'Observaciones Generales',
        }
        widgets = {
            'rutas': forms.Textarea(attrs={'rows': 3}),
            'observacion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Añadir observaciones si corresponde...'}),
        }

class InformeTecnicoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tramite
        fields = ['informe_tecnico', 'estado', 'observacion']

class InformeAndResolucionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tramite
        fields = ['informe_legal', 'resolucion_administrativa']

class DepositoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Deposito
        fields = ['numero', 'monto', 'fecha_deposito']
        labels = {
            'numero': 'Número de Boleta/Depósito',
            'monto': 'Monto Depositado (Bs.)',
            'fecha_deposito': 'Fecha del Depósito',
        }
        widgets = {
            'numero': forms.TextInput(attrs={'placeholder': 'Ej. 987654321'}),
            'monto': forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0.00'}),
            'fecha_deposito': forms.DateInput(attrs={'type': 'date'}),
        }