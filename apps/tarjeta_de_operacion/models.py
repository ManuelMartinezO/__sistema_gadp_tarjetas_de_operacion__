from django.db import models
from apps.tramite.models import Tramite
from apps.operador.models import Operador
from apps.afiliado.models import Afiliado
from apps.vehiculo.models import Vehiculo

# Create your models here.
class Ruta(models.Model):
    ruta = models.CharField(max_length=200)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ruta

class TarjetaDeOperacion(models.Model):

    TIPO_TARJETA = (
        ('001','InterProvincial'),
        ('002','Interprov.ATL'),
        ('003','Interprov.Confederado'),
        ('004','Interprov.Confe.SCZ'),
        ('005','Interprov.Cooperativas'),
    )

    TIEMPO = (
        ('year', 'AÑO'),
        ('month', 'MES'),
    )

    tramite = models.ForeignKey(
        Tramite,
        on_delete=models.CASCADE,
        related_name='tarjetas_de_operacion'
    )
    operador = models.ForeignKey(
        Operador,
        on_delete=models.PROTECT,
        related_name='tarjetas_de_operacion'
    )
    afiliado = models.ForeignKey(
        Afiliado,
        on_delete=models.PROTECT,
        related_name='tarjetas_de_operacion'
    )
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        related_name='tarjetas_de_operacion'
    )

    tipo_tarjeta = models.CharField(max_length=3, choices=TIPO_TARJETA)
    validez_periodo = models.CharField(max_length=10, choices=TIEMPO, default='year')
    validez_tiempo = models.PositiveIntegerField(default=1)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_emision = models.DateField(blank=True, null=True)
    valida_hasta = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.id} - {self.tramite.numero_tramite} - {self.tipo_tarjeta}"

class Recorrido(models.Model):
    tarjeta_operacion = models.ForeignKey(
        TarjetaDeOperacion,
        on_delete=models.CASCADE,
        related_name='recorridos'
    )
    ruta = models.ForeignKey(
        Ruta,
        on_delete=models.PROTECT,
        related_name='recorridos'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tarjeta_operacion.tipo_tarjeta} - {self.ruta.ruta}"