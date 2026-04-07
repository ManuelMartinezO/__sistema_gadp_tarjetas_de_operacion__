from django import forms
from .models import TarjetaDeOperacion, Ruta

class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = ['ruta']
        # widgets = {
        #     'ruta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Potosí - Uyuni'}),
        # }

# class RecorridoForm(forms.ModelForm):
#     class Meta:
#         model = Recorrido
#         fields = ['tarjeta_operacion', 'ruta']
#         widgets = {
#             'tarjeta_operacion': forms.Select(attrs={'class': 'form-select'}),
#             'ruta': forms.Select(attrs={'class': 'form-select'}),
#         }


# =======================================================
# 5. TARJETA DE OPERACIÓN (El formulario avanzado)
# =======================================================
class TarjetaDeOperacionForm(forms.ModelForm):
    class Meta:
        model = TarjetaDeOperacion
        fields = ['operador', 
                  'afiliado', 
                  'vehiculo', 
                  'tipo_tarjeta', 
                  'monto',
                  'validez_periodo', 
                  'validez_tiempo']
        
    #     widgets = {
    #         # 'tramite': forms.Select(attrs={'class': 'form-select'}),
    #         # ID específicos para el script de AJAX
    #         'operador': forms.Select(attrs={'class': 'form-select', 'id': 'id_operador'}),
    #         'afiliado': forms.Select(attrs={'class': 'form-select', 'id': 'id_afiliado'}),
    #         'vehiculo': forms.Select(attrs={'class': 'form-select'}),
    #         'tipo_tarjeta': forms.Select(attrs={'class': 'form-select'}),
    #         'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
    #         'validez_periodo': forms.Select(attrs={'class': 'form-select'}),
    #         'validez_tiempo': forms.NumberInput(attrs={'class': 'form-control'}),
    #     }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['operador'].empty_label = "Seleccione un Operador"
    #     self.fields['afiliado'].empty_label = "Seleccione un Afiliado"
    #     self.fields['vehiculo'].empty_label = "Seleccione un Vehículo"