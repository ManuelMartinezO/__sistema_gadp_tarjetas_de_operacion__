from django.db import models
from apps.tramite.models import Tramite
from apps.operador.models import Operador
from apps.afiliado.models import Afiliado
from apps.vehiculo.models import Vehiculo
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class TarjetaDeOperacion(models.Model):

    tramite = models.ForeignKey(
        Tramite,
        on_delete=models.CASCADE,
        related_name='tarjeta_tramite'
    )
    operador = models.ForeignKey(
        Operador,
        on_delete=models.PROTECT,
        related_name='tarjeta_operador'
    )
    afiliado = models.ForeignKey(
        Afiliado,
        on_delete=models.PROTECT,
        related_name='tarjeta_afiliado'
    )
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        related_name='tarjeta_vehiculo'
    )

    ruta = models.TextField()
    licencia = models.CharField(max_length=100)
    validez = models.PositiveIntegerField(default=1)
    monto = models.DecimalField(max_digits=8, decimal_places=2, default=40.00)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_emision = models.DateField(blank=True, null=True)
    valida_hasta = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.id} - {self.tramite.numero} - {self.licencia}"
