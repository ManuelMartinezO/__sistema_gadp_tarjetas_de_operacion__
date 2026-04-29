from django.db import models
from apps.afiliado.models import Afiliado

class MarcaVehiculo(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class TipoVehiculo(models.Model):
    tipo = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tipo

class Vehiculo(models.Model):

    TRANSPORTE = (
        ('p', 'PASAJEROS'),
        ('c', 'CARGA'),
    )

    # === RELACIONES ===
    afiliado = models.ForeignKey(
        Afiliado,
        on_delete=models.PROTECT,
        related_name='vehiculo_afiliado'
    )
    marca = models.ForeignKey(
        MarcaVehiculo,
        on_delete=models.PROTECT,
        related_name='vehiculo_marca'
    )
    tipo = models.ForeignKey(
        TipoVehiculo,
        on_delete=models.PROTECT,
        related_name='vehiculo_tipo'
    )

    # === FORMULARIO ===
    propietario = models.CharField(max_length=500, blank=True)
    transporte = models.CharField(max_length=20, choices=TRANSPORTE)
    modelo = models.PositiveIntegerField()
    placa = models.CharField(max_length=7, unique=True)
    chasis = models.CharField(max_length=100, unique=True)
    capacidad = models.PositiveIntegerField()
    
    # === FECHA ===
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.placa

