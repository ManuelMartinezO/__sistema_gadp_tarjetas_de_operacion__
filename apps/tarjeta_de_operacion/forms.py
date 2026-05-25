from django import forms
from .models import TarjetaDeOperacion

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'form-check-input',
                })
            else:
                widget_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
                field.widget.attrs.update({
                    'class': widget_class,
                    'style': 'border-radius: 10px;'
                })

class EditarVistaTarjetaForm(BootstrapFormMixin, forms.ModelForm):
    # El campo virtual para el afiliado se mantiene intacto
    nombre_afiliado = forms.CharField(
        max_length=200, 
        required=True,
        label='Afiliado Vinculado',
        widget=forms.TextInput(attrs={
            'list': 'lista_afiliados', 
            'autocomplete': 'off',
            'placeholder': 'Escriba para buscar el afiliado...'
        })
    )

    class Meta:
        model = TarjetaDeOperacion
        # MAGIA: Solo dejamos 'ruta', ya que es el único campo real del modelo que quieres editar aquí
        fields = ['ruta'] 
        
        labels = {
            'ruta': 'Descripción de la Ruta',
        }
        widgets = {
            'ruta': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Describa el recorrido aprobado...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Precargar el nombre del afiliado actual si se está editando una tarjeta existente
        if self.instance and self.instance.pk and self.instance.afiliado:
            self.fields['nombre_afiliado'].initial = self.instance.afiliado.nombre_completo

class EditarTarjetaForm(BootstrapFormMixin, forms.ModelForm):
    # Campo de texto libre para buscar y vincular al afiliado mediante un datalist
    nombre_afiliado = forms.CharField(
        max_length=200, 
        required=True,
        label='Afiliado Vinculado',
        widget=forms.TextInput(attrs={
            'list': 'lista_afiliados', 
            'autocomplete': 'off',
            'placeholder': 'Escriba para buscar el afiliado...'
        })
    )

    class Meta:
        model = TarjetaDeOperacion
        # Retiramos 'afiliado' directo ya que lo manejamos desde 'nombre_afiliado' en la vista
        fields = [
            'tramite', 'estado', 'operador', 'vehiculo', 
            'ruta', 'licencia', 'validez', 'monto', 
            'fecha_emision', 'valida_hasta'
        ]
        labels = {
            'tramite': 'Trámite Asociado',
            'ruta': 'Descripción de la Ruta',
            'validez': 'Años de Validez',
        }
        widgets = {
            'ruta': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Describa el recorrido aprobado...'}),
            'fecha_emision': forms.DateInput(attrs={'type': 'date'}),
            'valida_hasta': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Precargar el nombre del afiliado actual si se está editando una tarjeta existente
        if self.instance and self.instance.pk and self.instance.afiliado:
            self.fields['nombre_afiliado'].initial = self.instance.afiliado.nombre_completo

class TarjetaDeOperacionForm(BootstrapFormMixin, forms.ModelForm):
    """
    Formulario de creación inicial para la Tarjeta de Operación.
    Actualmente sin campos expuestos; asegúrate de definir los 'fields' requeridos 
    cuando actives la vista de creación.
    """
    class Meta:
        model = TarjetaDeOperacion
        fields = [] # TODO: Añadir campos según los requisitos de negocio al crear