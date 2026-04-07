from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Perfil

class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', 'style': 'border-radius: 10px;'})

class UsuarioForm(BootstrapFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = UserCreationForm.Meta.fields + ('rol',)

class PerfilForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['nombre', 'apellido', 'ci', 'email', 'numero_celular']