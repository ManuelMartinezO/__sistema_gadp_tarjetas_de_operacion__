from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

class RegistroForm(UserCreationForm):
    class Meta:
        model = Usuario
        # No incluimos 'password' aquí porque UserCreationForm ya añade 
        # automáticamente los campos 'Contraseña' y 'Confirmar contraseña'
        fields = [
            'username', 'email', 'nombre', 'apellido', 
            'numero_carnet_ci', 'numero_celular'
        ]