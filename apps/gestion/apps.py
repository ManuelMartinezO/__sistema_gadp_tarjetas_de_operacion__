from django.apps import AppConfig


class GestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.gestion'
    def ready(self):
        # 2. Importas el archivo signals justo aquí adentro
        import apps.gestion.signals
