from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario (AbstractUser):
    ROLES = (
        ('sa', 'Super Administrador'),
        ('a', 'Administrador'),
        ('u', 'Usuario')
    )
    rol = models.CharField(max_length=2, choices=ROLES, default='u')
    
    def __str__(self):
        return self.username

class Perfil (models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=200)
    ci = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    numero_celular = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.nombre
