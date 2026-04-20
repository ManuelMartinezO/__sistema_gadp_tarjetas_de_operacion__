from django.urls import path
from .views import historial_list_view, logup_view
from apps.usuario.views import usuario_list, crear_usuario, usuario_detail, editar_usuario, eliminar_usuario
from . import views

app_name = 'gestion'

urlpatterns = [
    # La ruta será: midominio.com/gestion/auditoria/ (o el prefijo que definas en el urls.py principal)
    path('auditoria/', historial_list_view, name='historial_list'),
    path('logup/', logup_view, name='logup'),
    path('usuarios/', usuario_list, name='usuario_list'),
    path('usuarios/crear/', crear_usuario, name='crear_usuario'),
    path('usuarios/<int:pk>/', usuario_detail, name='usuario_detail'),
    path('usuarios/<int:pk>/editar/', editar_usuario, name='editar_usuario'),
    path('usuarios/<int:pk>/eliminar/', eliminar_usuario, name='eliminar_usuario'),
    path('operadores/', views.operador_list, name='operador_list'),
    path('operadores/crear/', views.crear_operador, name='crear_operador'),
    path('operadores/<int:pk>/editar/', views.editar_operador, name='editar_operador'),
    path('operadores/<int:pk>/eliminar/', views.eliminar_operador, name='eliminar_operador'),
]