from django import forms
from apps.operador.models import Operador

class OperadorForm(forms.ModelForm):
    class Meta:
        model = Operador
        fields = ('nombre',)
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Sindicato de Transporte 10 de Noviembre'}),
        }