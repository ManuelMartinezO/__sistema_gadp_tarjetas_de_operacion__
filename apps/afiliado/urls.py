from django.urls import path
from . import views

app_name='afiliado'

urlpatterns = [
    path('afiliados/', views.lista_afiliados, name='lista_afiliados'),
    path('afiliado/crear/', views.crear_afiliado, name='crear_afiliado'),
    path('afiliado/detalle/<int:id_afiliado>/', views.detalle_afiliado, name='detalle_afiliado'),
]