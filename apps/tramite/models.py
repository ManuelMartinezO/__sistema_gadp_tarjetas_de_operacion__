from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from apps.operador.models import Operador

# ===== CLASE TRAMITE =====
class Tramite(models.Model):

    TIPO = (
        ('o', 'Otorgación Nueva de Tarjetas de Operación'),
        ('r', 'Renovación de Tarjetas de Operación'),
    )
    ESTADO = (
        ('p', 'PENDIENTE'),
        ('v', 'VALIDO'),
        ('o', 'OBSERVADO'),
    )
    LICENCIA = (
        ('l1','InterProvincial'),
        ('l2','Interprov.ATL'),
        ('l3','Interprov.Confederado'),
        ('l4','Interprov.Confe.SCZ'),
        ('l5','Interprov.Cooperativas'),
    )

    # === CHOICES ===
    tipo = models.CharField(max_length=1, choices=TIPO)
    estado = models.CharField(max_length=1, choices=ESTADO, default='p')
    segunda_revicion = models.CharField(max_length=1, choices=ESTADO, default='p')
    licencia = models.CharField(max_length=2, choices=LICENCIA)
    
    # === RELACIONES ===
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='tramite_usuario'
    )
    operador = models.ForeignKey(
        Operador,
        on_delete=models.PROTECT,
        related_name="tramite_operador"
    )

    # === DOCUMENTOS, INFORMES, RESOLUCIONES ===
    informe_tecnico = models.FileField(
        upload_to='informes_tecnicos/', 
        blank=True, 
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
    )
    informe_legal = models.FileField(
        upload_to='informes_legales/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    resolucion_administrativa = models.FileField(
        upload_to='resolucion_administrativa/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )

    # === AUTO ===
    numero = models.PositiveIntegerField(unique=True)
    deposito = models.BooleanField(default=False)
    
    # === FORMULARIO ===
    fojas = models.PositiveIntegerField(blank=True, null=True)
    rutas = models.TextField()
    observacion = models.TextField(blank=True, null=True)

    # === FECHA AUTO/FORM ===
    fecha_registro = models.DateTimeField(auto_now_add=True)

    # === BANCO ===
    banco = models.CharField(max_length=100, blank=True, null=True, default='BANCO UNION')
    cuenta = models.CharField(max_length=50, blank=True, null=True, default='1-6024553')

    # === FIRMA ===
    encargado_firma_1 = models.CharField(max_length=100, blank=True, null=True, default='Abog. Heber Rodriguez Flores')
    area_firma_1 = models.CharField(max_length=100, blank=True, null=True, default='SECRETARIO DEPARTAMENTAL DE JURÍDICA')
    encargado_firma_2 = models.CharField(max_length=100, blank=True, null=True, default='Oscar Mendoza Mamani')
    area_firma_2 = models.CharField(max_length=100, blank=True, null=True, default='SECRETARIO DEPARTAMENTAL DE COORDINACIÓN GENERAL')

    # === FUNCIONES EXTRAS ===
    # ==== INICIAR EL DOCUMENTO DESDE EL NUMERO 2000 ====
    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo_tramite = Tramite.objects.order_by('-numero').first()
            
            if ultimo_tramite and ultimo_tramite.numero:
                self.numero = ultimo_tramite.numero + 1
            else:
                self.numero = 2000
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Trámite N° {self.numero} - Usuario: {self.usuario.username}"

# ===== CLASE DEPOSITO =====
class Deposito(models.Model):
    
    # === RELACIONES ===
    tramite = models.ForeignKey(
        Tramite, 
        on_delete=models.CASCADE, 
        related_name='deposito_tramite'
    )
    
    # === FORMULARIO ===
    numero = models.CharField(max_length=50, unique=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    
    # === FECHA AUTO/FORM ===
    fecha_deposito = models.DateTimeField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Deposito: {self.numero} - Monto: {self.monto}"
    