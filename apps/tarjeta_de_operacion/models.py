from django.db import models
from apps.tramite.models import Tramite
from apps.operador.models import Operador
from apps.afiliado.models import Afiliado
from apps.vehiculo.models import Vehiculo
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class Ruta(models.Model):
    ruta = models.CharField(max_length=500)
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
        related_name='tramites_tarjeta'
    )
    operador = models.ForeignKey(
        Operador,
        on_delete=models.PROTECT,
        related_name='operadores_tarjeta'
    )
    afiliado = models.ForeignKey(
        Afiliado,
        on_delete=models.PROTECT,
        related_name='afiliados_tarjeta'
    )
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.PROTECT,
        related_name='vehiculos_tarjeta'
    )
    ruta = models.ForeignKey(
        Ruta,
        on_delete=models.PROTECT,
        related_name='rutas_tarjeta'
    )

    tipo_tarjeta = models.CharField(max_length=3, choices=TIPO_TARJETA)
    validez_periodo = models.CharField(max_length=10, choices=TIEMPO, default='year')
    validez_tiempo = models.PositiveIntegerField(default=1)
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=40)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_emision = models.DateField(blank=True, null=True)
    valida_hasta = models.DateField(blank=True, null=True)
    hora_recorrido = models.CharField(max_length=100)
    viceversa = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # 1. Detectar si es una tarjeta nueva ANTES de guardar
        es_nuevo = self.pk is None 
        
        if es_nuevo: 
            # 2. Lógica de fechas (solo si es nuevo)
            if not self.fecha_emision:
                self.fecha_emision = timezone.localdate()

            if self.validez_periodo == 'year':
                delta = relativedelta(years=self.validez_tiempo)
            elif self.validez_periodo == 'month':
                delta = relativedelta(months=self.validez_tiempo)
            else:
                delta = relativedelta(days=0)

            self.valida_hasta = self.fecha_emision + delta

        # 3. Guardar en la base de datos (Esto genera el ID/pk de la tarjeta)
        super().save(*args, **kwargs)
        
        # 4. Crear el registro del Recorrido (DESPUÉS de que la tarjeta ya tiene ID)
        if es_nuevo:
            # Importar Recorrido aquí si da error de importación circular al inicio del archivo
            # from .models import Recorrido 
            Recorrido.objects.create(
                tarjeta_operacion=self,
                ruta=self.ruta
            )

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