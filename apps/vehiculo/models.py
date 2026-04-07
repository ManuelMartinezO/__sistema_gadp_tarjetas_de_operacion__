from django.db import models
from apps.afiliado.models import Afiliado

# Create your models here.
class MarcaVehiculo(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class ColorVehiculo(models.Model):
    nombre = models.CharField(max_length=50)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class TipoVehiculo(models.Model):
    tipo = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tipo

class Vehiculo(models.Model):

    TIPO_TRANSPORTE = (
        ('pasajeros', 'PASAJEROS'),
        ('carga', 'CARGA'),
    )

    marca = models.ForeignKey(
        MarcaVehiculo,
        on_delete=models.PROTECT,
        related_name='vehiculos'
    )

    color = models.ForeignKey(
        ColorVehiculo,
        on_delete=models.PROTECT,
        related_name='vehiculos'
    )

    tipo_vehiculo = models.ForeignKey(
        TipoVehiculo,
        on_delete=models.PROTECT,
        related_name='vehiculos'
    )

    propietario = models.ForeignKey(
        Afiliado,
        on_delete=models.PROTECT,
    )

    tipo_transporte = models.CharField(max_length=20, choices=TIPO_TRANSPORTE, default='pasajeros')

    modelo = models.PositiveIntegerField()
    placa = models.CharField(max_length=20, unique=True)
    chasis = models.CharField(max_length=100, unique=True)
    capacidad = models.PositiveIntegerField()
    
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.placa

