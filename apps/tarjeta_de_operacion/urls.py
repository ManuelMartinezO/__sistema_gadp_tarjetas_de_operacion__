from django.urls import path
from . import views

app_name = 'tarjeta'

urlpatterns = [
    path('tarjetas/', views.lista_tarjetas, name='lista_tarjetas'),
    path('tarjeta/detalle/<int:id_tarjeta>', views.detalle_tarjeta, name='detalle_tarjeta'),
    path('tarjeta/editar/<int:id_tarjeta>/', views.editar_tarjeta, name='editar_tarjeta'),
    path('tarjeta/pdf/<int:id_tarjeta>/', views.generar_pdf_tarjeta, name='tarjeta_pdf'),
    path('crear-ruta-ajax/', views.crear_ruta_ajax, name='crear_ruta_ajax'),
]