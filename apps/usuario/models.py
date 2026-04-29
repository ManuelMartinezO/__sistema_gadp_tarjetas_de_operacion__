from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver

class UsuarioManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'sa')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

class Usuario(AbstractUser):
    ROLES = (
        ('sa', 'Super Administrador'),
        ('a', 'Administrador'),
        ('u', 'Tecnico')
    )
    rol = models.CharField(max_length=2, choices=ROLES, default='u')
    objects = UsuarioManager()

    def __str__(self):
        return self.username

class Perfil(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil')
    nombre = models.CharField(max_length=100, blank=True)
    apellido = models.CharField(max_length=200, blank=True)
    # Importante: null=True y blank=True para que no truene al crear superusuario
    ci = models.CharField(max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    numero_celular = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"

# --- SIGNALS PARA NO ROMPER LA APP ---

@receiver(post_save, sender=Usuario)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea un perfil automáticamente cuando se crea un Usuario"""
    if created:
        Perfil.objects.create(usuario=instance)

@receiver(post_save, sender=Usuario)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Actualiza el perfil automáticamente cuando se guarda el Usuario"""
    instance.perfil.save()