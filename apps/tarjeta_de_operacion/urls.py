from django.urls import path
from . import views

app_name = 'tarjeta'

urlpatterns = [
    path('tarjetas/', views.lista_tarjetas, name='lista_tarjetas'),
    path('tarjeta/detalle/<int:id_tarjeta>', views.detalle_tarjeta, name='detalle_tarjeta'),
   
]