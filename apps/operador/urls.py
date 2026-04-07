from django.urls import path
from . import views

app_name='operador'

urlpatterns = [
    path('operadores/', views.lista_operadores, name='lista_operadores'),
    path('operador/crear/', views.crear_operador, name='crear_operador'),
    path('operador/detalle/<int:id_operador>/', views.detalle_operador, name='detalle_operador'),
]