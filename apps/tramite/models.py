from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from apps.operador.models import Operador

class Tramite(models.Model):

    TIPO_TRAMITE = (
        ('otorgacion', 'Otorgación Nueva de Tarjetas de Operación'),
        ('renovacion', 'Renovación de Tarjetas de Operación'),
    )

    ESTADO_TRAMITE = (
        ('pendiente', 'Tramite Pendiente'),
        ('validado', 'Tramite Validado'),
        ('observado', 'Tramite Observado'),
    )
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
    )

    operador = models.ForeignKey(
        Operador,
        on_delete=models.PROTECT,
        related_name="tarjetas_de_operacion"
    )

    tramite_file = models.FileField(
        upload_to='tramites/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
    )
    reporte_file = models.FileField(
        upload_to='reportes/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    
    numero_tramite = models.PositiveIntegerField(unique=True)
    estado_deposito = models.BooleanField(default=False)
    fojas = models.PositiveIntegerField(blank=True, null=True)

    tipo_tramite = models.CharField(max_length=20, choices=TIPO_TRAMITE)
    estado_tramite = models.CharField(max_length=20, choices=ESTADO_TRAMITE, default='pendiente')
    
    fecha_validacion = models.DateTimeField(blank=True, null=True)
    fecha_observacion = models.DateTimeField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.numero_tramite:
            ultimo_tramite = Tramite.objects.order_by('-numero_tramite').first()
            
            if ultimo_tramite and ultimo_tramite.numero_tramite:
                self.numero_tramite = ultimo_tramite.numero_tramite + 1
            else:
                self.numero_tramite = 2000
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Trámite N° {self.numero_tramite} - Usuario: {self.usuario.username}"

class Deposito(models.Model):
    
    tramite = models.OneToOneField(
        Tramite, 
        on_delete=models.CASCADE, 
        related_name='deposito'    
    )
    
    numero_deposito = models.CharField(max_length=50, unique=True)
    monto_deposito = models.DecimalField(max_digits=10, decimal_places=2)
    
    fecha_deposito = models.DateTimeField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Deposito: {self.numero_deposito} - Monto: {self.monto_deposito}"
    