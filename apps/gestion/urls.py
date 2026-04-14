from django.urls import path
from . import views

app_name = 'gestion'

urlpatterns = [
    # La ruta será: midominio.com/gestion/auditoria/ (o el prefijo que definas en el urls.py principal)
    path('auditoria/', views.historial_list_view, name='historial_list'),
]   