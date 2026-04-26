from django.db import models

# Create your models here.
class Operador(models.Model):
    organizacion = models.ForeignKey(
        'Organizacion',
        on_delete=models.PROTECT,
        related_name='operador_organizacion'
    )
    federacion = models.ForeignKey(
        'Federacion',
        on_delete=models.PROTECT,
        related_name='operador_federacion'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.organizacion.nombre} - {self.federacion.nombre}"

class Organizacion(models.Model):
    nombre = models.CharField(max_length=500)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre
    
class Federacion(models.Model):
    nombre = models.CharField(max_length=500)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre