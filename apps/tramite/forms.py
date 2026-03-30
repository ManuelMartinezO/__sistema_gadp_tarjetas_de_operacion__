from django import forms
from .models import Tramite, Deposito

class TramiteForm(forms.ModelForm):
    class Meta:
        model = Tramite
        # Son los mismos campos que pusimos en las Vistas (Views)
        fields = [
            'usuario', 'tipo_tramite', 'estado_tramite', 
            'estado_deposito', 'tramite_file', 'reporte_file'
        ]
        
        # Le damos nombres más amigables para el usuario
        labels = {
            'usuario': 'Propietario del Trámite',
            'tipo_tramite': 'Tipo de Solicitud',
            'estado_tramite': 'Estado de Validación',
            'estado_deposito': '¿El depósito ha sido verificado?',
            'tramite_file': 'Documento del Trámite (PDF/Imagen)',
            'reporte_file': 'Reporte Adjunto (Opcional)',
        }

        # Inyectamos clases de Bootstrap para que se vea hermoso
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-select'}),
            'tipo_tramite': forms.Select(attrs={'class': 'form-select'}),
            'estado_tramite': forms.Select(attrs={'class': 'form-select'}),
            'estado_deposito': forms.CheckboxInput(attrs={'class': 'form-check-input fs-4 ms-1'}),
            'tramite_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'reporte_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class DepositoForm(forms.ModelForm):
    class Meta:
        model = Deposito
        fields = ['tramite', 'numero_deposito', 'monto_deposito', 'fecha_deposito']
        
        labels = {
            'tramite': 'Trámite Asociado',
            'numero_deposito': 'Número de Comprobante / Transacción',
            'monto_deposito': 'Monto Depositado (Bs.)',
            'fecha_deposito': 'Fecha y Hora del Depósito',
        }

        widgets = {
            'tramite': forms.Select(attrs={'class': 'form-select'}),
            'numero_deposito': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej. 0987654321'
            }),
            'monto_deposito': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.10', # Permite decimales
                'placeholder': '0.00'
            }),
            # type='datetime-local' abre un calendario nativo súper bonito en el navegador
            'fecha_deposito': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            }),
        }


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