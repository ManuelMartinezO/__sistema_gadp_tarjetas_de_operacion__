from django import forms
from .models import Tramite, Deposito
from apps.usuario.models import Usuario

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', 'style': 'border-radius: 10px;'})

class NuevoTramiteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Tramite
        fields = [
            'usuario',
            'operador',
            'tipo',
            'licencia',
            'fojas',
            'rutas',
        ]

class InformeTecnicoForm(forms.ModelForm):
    class Meta:
        model = Tramite
        fields = [
            'informe_tecnico',
            'estado',
            'observacion',
        ]

class InformeAndResolucionForm(forms.ModelForm):
    class Meta:
        model = Tramite
        fields = [
            'informe_legal',
            'resolucion_administrativa',
        ]

class DepositoForm(forms.ModelForm):
    class Meta:
        model = Deposito
        fields = [
            'numero', 
            'monto', 
            'fecha_deposito',
        ]
        widgets = {
            'fecha_deposito': forms.DateInput(
                # format='%Y-%m-%d' # Opcional: si necesitas un formato específico al cargar
                attrs={
                    'type': 'date', # Esto renderiza el calendario HTML5
                }
            ),
        }





# class TramiteEviadoForm(BootstrapFormMixin, forms.ModelForm):
#     class Meta:
#         model = Tramite
#         fields = [
#             'usuario',
#             'operador',
#             'fojas',
#             'tipo_tramite',
#             'tramite_file',
#         ]
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
        
#         # Sobrescribimos el queryset del campo 'usuario' para filtrar solo por rol 'u'
#         if 'usuario' in self.fields:
#             self.fields['usuario'].queryset = Usuario.objects.filter(rol='u', is_active=True)

# class EditarTramiteForm(BootstrapFormMixin, forms.ModelForm):
#     class Meta:
#         model = Tramite
#         fields = [
#             'usuario',
#             'tipo_tramite',
#         ]

# class EditarInformeForm(BootstrapFormMixin, forms.ModelForm):
#     class Meta:
#         model = Tramite
#         fields = [
#             'tramite_file'
#         ]

# class EditarReporteForm(BootstrapFormMixin, forms.ModelForm):
#     class Meta:
#         model = Tramite
#         fields = [
#             'reporte_file'
#         ]

# class EditarEstadoForm(BootstrapFormMixin, forms.ModelForm):
#     class Meta:
#         model = Tramite
#         fields = [
#             'estado_tramite'
#         ]

# class TramiteReportadoForm(BootstrapFormMixin, forms.ModelForm):
#     class Meta:
#         model = Tramite
#         fields = [
#             'reporte_file',
#             'estado_tramite',
#         ]
