from django.urls import path
from . import views

app_name='operador'

urlpatterns = [
    path('operadores/', views.lista_operadores, name='lista_operadores'),
    path('operador/detalle/<int:id_operador>/', views.detalle_operador, name='detalle_operador'),
    path('operador/<int:operador_id>/reporte-pdf/', views.descargar_reporte_operador_pdf, name='reporte_pdf'),
]