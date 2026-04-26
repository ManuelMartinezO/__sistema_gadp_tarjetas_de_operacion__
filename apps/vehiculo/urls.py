from django.urls import path
from . import views

app_name='vehiculo'

urlpatterns = [
    path('vehiculos/', views.lista_vehiculos, name='lista_vehiculos'),
    path('vehiculo/detalle/<str:placa>/', views.detalle_vehiculo, name='detalle_vehiculo'),
]