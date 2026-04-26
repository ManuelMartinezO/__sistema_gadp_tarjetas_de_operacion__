
from django.db import models
from django.conf import settings

from auditlog.registry import auditlog

from apps.operador.models import Operador
from apps.vehiculo.models import Vehiculo
from apps.afiliado.models import Afiliado
from apps.tarjeta_de_operacion.models import TarjetaDeOperacion
from apps.tramite.models import Tramite, Deposito
from apps.usuario.models import Usuario, Perfil

auditlog.register(Deposito)
auditlog.register(Operador)
auditlog.register(Vehiculo)
auditlog.register(Afiliado)
auditlog.register(TarjetaDeOperacion)
auditlog.register(Tramite)
auditlog.register(Usuario)
auditlog.register(Perfil)

class HistorialAccion(models.Model):
    # Tipos de acciones predefinidas
    ACCIONES = (
        ('LOGIN', 'Ingreso al sistema'),
        ('LOGOUT', 'Salida del sistema'),
        ('CREAR', 'Creación de registro'),
        ('EDITAR', 'Edición de registro'),
        ('ELIMINAR', 'Eliminación de registro'),
        ('IMPRIMIR', 'Impresión de documento'),
        ('OTRO', 'Otra acción'),
    )

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    descripcion = models.TextField() # Ejemplo: "Editó los datos de la línea de transporte de la Zona Sur"
    modelo_afectado = models.CharField(max_length=50, blank=True, null=True) # Ejemplo: "Operador" o "Vehiculo"
    id_registro = models.PositiveIntegerField(blank=True, null=True) # El ID del objeto modificado
    ip_usuario = models.GenericIPAddressField(blank=True, null=True) # Útil para seguridad
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial de Acción"
        verbose_name_plural = "Historial de Acciones"
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.fecha_hora}"