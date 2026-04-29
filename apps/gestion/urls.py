from django.urls import path
from .views import historial_list_view, logup_view
from apps.usuario.views import usuario_list, crear_usuario, usuario_detail, editar_usuario, eliminar_usuario
from . import views

app_name = 'gestion'

urlpatterns = [
    path('auditoria/', historial_list_view, name='historial_list'),
    path('logup/', logup_view, name='logup'),
    path('usuarios/', usuario_list, name='usuario_list'),
    path('usuarios/crear/', crear_usuario, name='crear_usuario'),
    path('usuarios/<int:pk>/', usuario_detail, name='usuario_detail'),
    path('usuarios/<int:pk>/editar/', editar_usuario, name='editar_usuario'),
    path('usuarios/<int:pk>/eliminar/', eliminar_usuario, name='eliminar_usuario'),
    path('operadores/crear/', views.crear_operador, name='crear_operador'),
    path('operadores/<int:pk>/editar/', views.editar_operador, name='editar_operador'),
    path('operadores/<int:pk>/eliminar/', views.eliminar_operador, name='eliminar_operador'),
    path('afiliados/', views.gestion_admin_afiliados, name='afiliado_list'),
    path('operadores/', views.gestion_operadores, name='operador_list'),
    path('federaciones/', views.gestion_federaciones, name='federacion_list'),
    path('organizaciones/', views.gestion_organizaciones, name='organizacion_list'),
    path('vehiculos/', views.gestion_vehiculos, name='vehiculo_list'),
    path('marcas/', views.gestion_marcas, name='marca_list'),
    path('tipos/', views.gestion_tipos, name='tipo_list'),
    path('tramites/', views.gestion_tramites, name='tramite_list'),
    path('tarjetas/', views.gestion_tarjetas, name='tarjeta_list'),
    path('reporte-general-pdf/', views.generar_reporte_pdf, name='reporte_general_pdf'),
]