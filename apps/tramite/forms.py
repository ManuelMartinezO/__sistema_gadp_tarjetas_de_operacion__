from django import forms
from .models import Tramite, Deposito

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', 'style': 'border-radius: 10px;'})

class TramiteEviadoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tramite
        fields = [
            'usuario',
            'tipo_tramite',
            'tramite_file',
        ]

class EditarTramiteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tramite
        fields = [
            'usuario',
            'tipo_tramite',
        ]

class EditarInformeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tramite
        fields = [
            'tramite_file'
        ]

class EditarReporteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tramite
        fields = [
            'reporte_file'
        ]

class EditarEstadoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tramite
        fields = [
            'estado_tramite'
        ]

class TramiteReportadoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tramite
        fields = [
            'reporte_file',
            'estado_tramite',
        ]

class DepositoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Deposito
        fields = ['numero_deposito', 
                  'monto_deposito', 
                  'fecha_deposito']
        widgets = {
            'fecha_deposito': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            }),
        }