from django.urls import path
from . import views

app_name='operador'

urlpatterns = [
    path('operadores/', views.lista_operadores, name='lista_operadores'),
    path('operador/crear/', views.crear_operador, name='crear_operador'),
    path('operador/detalle/<int:id_operador>/', views.detalle_operador, name='detalle_operador'),
    path('operador/editar/<int:id_operador>/', views.editar_operador, name='editar_operador'),
    path('operador/<int:operador_id>/reporte-pdf/', views.descargar_reporte_operador_pdf, name='reporte_pdf'),
]