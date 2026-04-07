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
        
        
        # labels = {
        #     'tramite': 'Trámite Asociado',
        #     'numero_deposito': 'Número de Comprobante / Transacción',
        #     'monto_deposito': 'Monto Depositado (Bs.)',
        #     'fecha_deposito': 'Fecha y Hora del Depósito',
        # }

        # widgets = {
        #     'tramite': forms.Select(attrs={'class': 'form-select'}),
        #     'numero_deposito': forms.TextInput(attrs={
        #         'class': 'form-control', 
        #         'placeholder': 'Ej. 0987654321'
        #     }),
        #     'monto_deposito': forms.NumberInput(attrs={
        #         'class': 'form-control', 
        #         'step': '0.10', # Permite decimales
        #         'placeholder': '0.00'
        #     }),
        #     # type='datetime-local' abre un calendario nativo súper bonito en el navegador
        #     'fecha_deposito': forms.DateTimeInput(attrs={
        #         'class': 'form-control', 
        #         'type': 'datetime-local'
        #     }),
        # }


# tramites/forms.py (Añade esto debajo de tu TramiteForm)

class TramiteEvaluacionForm(forms.ModelForm):
    """Formulario restringido SOLO para el rol 'usuario' (El Revisor)"""
    class Meta:
        model = Tramite
        # Solo le permitimos tocar el estado y subir su reporte
        fields = ['estado_tramite', 'reporte_file']
        
        labels = {
            'estado_tramite': 'Dictamen Técnico (Validar / Observar)',
            'reporte_file': 'Adjuntar Reporte de Evaluación (PDF/Imagen)',
        }

        widgets = {
            'estado_tramite': forms.Select(attrs={'class': 'form-select'}),
            'reporte_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }