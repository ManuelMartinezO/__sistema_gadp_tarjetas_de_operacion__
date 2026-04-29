from django.db.models.signals import post_save
from .middleware import get_current_user, get_current_request
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import HistorialAccion

# Capturar Login
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    HistorialAccion.objects.create(
        usuario=user,
        accion='LOGIN',
        descripcion='El usuario ha iniciado sesión en el sistema.',
        ip_usuario=ip
    )

# Capturar Logout
@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    HistorialAccion.objects.create(
        usuario=user,
        accion='LOGOUT',
        descripcion='El usuario ha cerrado sesión.',
        ip_usuario=ip
    )

# Suponiendo que tienes un modelo Operador
# from app_transporte.models import Operador 
@receiver(post_save)
def auditar_cambios_modelo(sender, instance, created, **kwargs):
    # 1. Ignorar la auditoría si es el propio modelo de Historial
    if sender == HistorialAccion:
        return

    # 2. NUEVO: Ignorar cualquier modelo que NO pertenezca a tu app 'gestion'
    # Esto evita que auditemos Sesiones de Django, ContentTypes, Migraciones, etc.
    if instance._meta.app_label != 'gestion':
        return

    usuario_actual = get_current_user()
    request_actual = get_current_request()
    ip = request_actual.META.get('REMOTE_ADDR') if request_actual else None

    if usuario_actual and usuario_actual.is_authenticated:
        accion = 'CREAR' if created else 'EDITAR'
        nombre_modelo = sender.__name__
        
        HistorialAccion.objects.create(
            usuario=usuario_actual,
            accion=accion,
            descripcion=f'Se ha {"creado" if created else "modificado"} un registro en {nombre_modelo}: {str(instance)}',
            modelo_afectado=nombre_modelo,
            
            # 3. MEJORA: Usar .pk en lugar de .id
            # .pk (Primary Key) siempre funciona, sin importar cómo se llame la llave primaria del modelo
            id_registro=instance.pk, 
            
            ip_usuario=ip
        )