from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.tarjeta_de_operacion.models import TarjetaDeOperacion # Asegúrate de que la ruta sea correcta

class Command(BaseCommand):
    help = 'Busca las tarjetas de operación emitidas cuya fecha ya expiró y las pasa a vencidas'

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        
        # Busca tarjetas que estén Emitidas ('e') Y su valida_hasta sea MENOR al día de hoy
        tarjetas_vencidas = TarjetaDeOperacion.objects.filter(
            estado='e',
            valida_hasta__lt=hoy
        )
        
        cantidad = tarjetas_vencidas.count()
        
        if cantidad > 0:
            # .update() hace el cambio directo en la base de datos de un solo golpe (muy rápido)
            tarjetas_vencidas.update(estado='v')
            self.stdout.write(self.style.SUCCESS(f'Éxito: Se actualizaron {cantidad} tarjetas a estado VENCIDA.'))
        else:
            self.stdout.write(self.style.SUCCESS('No se encontraron tarjetas para vencer hoy.'))