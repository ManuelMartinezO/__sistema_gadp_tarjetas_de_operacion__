from django.db import models
from apps.operador.models import Operador
# Create your models here.
class Afiliado(models.Model):
    operador = models.ForeignKey(
        Operador,
        on_delete=models.PROTECT,
        related_name='afiliado_operador'
    )
    nombre_completo = models.CharField(max_length=500)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_completo