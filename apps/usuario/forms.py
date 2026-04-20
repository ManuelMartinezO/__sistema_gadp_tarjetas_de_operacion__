from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
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

class UsuarioCreationForm(UserCreationForm):
    """
    Hereda de UserCreationForm para garantizar que el campo 'password' 
    se encripte (hash) correctamente en la base de datos.
    """
    class Meta(UserCreationForm.Meta):
        model = Usuario
        # El campo password ya lo incluye UserCreationForm por defecto
        fields = ('username', 'rol', 'is_active') 


class UsuarioUpdateForm(UserChangeForm):
    """
    Hereda de UserChangeForm. Quitamos el campo password para que 
    el SuperAdmin edite roles o active/desactive cuentas sin tocar la clave.
    """
    password = None  # Oculta el campo de contraseña en la edición básica
    
    class Meta:
        model = Usuario
        fields = ('username', 'rol', 'is_active')


# ==========================================
# FORMULARIO PARA PERFIL (Datos Personales)
# ==========================================

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ('nombre', 'apellido', 'ci', 'email', 'numero_celular')
        
        # Excluimos explícitamente el campo 'usuario' porque ese enlace 
        # lo hacemos nosotros manualmente por debajo (en la vista) al guardar.
        exclude = ('usuario',)