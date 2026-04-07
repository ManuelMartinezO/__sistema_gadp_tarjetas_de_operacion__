from django.db import models

# Create your models here.
class Operador(models.Model):
    nombre = models.CharField(max_length=500)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre