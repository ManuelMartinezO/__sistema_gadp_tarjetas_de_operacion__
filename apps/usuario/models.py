from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager


# Create your models here.
class Usuario(AbstractBaseUser, PermissionsMixin):

    ROLES = (
        ('super_administrador', 'Super Administrador'),
        ('administrador', 'Administrador'),
        ('usuario', 'Usuario')
    )

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=200)
    numero_carnet_ci = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    numero_celular = models.CharField(max_length=20, unique=True)
    username = models.CharField(max_length=200, unique=True)
    rol_usuario = models.CharField(max_length=20, choices=ROLES, default='usuario')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['nombre', 'apellido', 'numero_carnet_ci', 'email', 'numero_celular']

    def __str__(self):
        return f"{self.username} ({self.numero_carnet_ci})"
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'