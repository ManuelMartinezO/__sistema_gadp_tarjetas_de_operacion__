from django import forms
from .models import Operador

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', 'style': 'border-radius: 10px;'})

class NuevoOperadorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Operador
        fields = ['nombre']

class OperadorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Operador
        fields = ['nombre']