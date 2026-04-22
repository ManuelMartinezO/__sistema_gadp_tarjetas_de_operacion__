from django import forms
from .models import TarjetaDeOperacion

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Verificamos si el widget es un Checkbox
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input', # Clase correcta para checkbox
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'style': 'border-radius: 10px;'
                })



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
class TarjetaDeOperacionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TarjetaDeOperacion
        fields = [
                #   'afiliado', 
                # #   'vehiculo', 
                # #   'tipo_tarjeta',
                # #   'ruta',
                # #   'hora_recorrido',
                # #   'viceversa',
                # #   'monto',
                # #   'validez_periodo', 
                #   'validez_tiempo'
                  ]
        # widgets = {
        #     'viceversa': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        # }
        
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