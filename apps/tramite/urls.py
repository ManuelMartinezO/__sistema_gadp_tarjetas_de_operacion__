from django.urls import path, include
from . import views

app_name = 'tramite'

urlpatterns = [
    path('tramites/', views.lista_tramites, name='lista_tramites'),
    path('tramite/nuevo/', views.crear_tramite, name='crear_tramite'),
    path('tramite/<int:numero_tramite>/', views.detalle_tramite, name='detalle_tramite'),
    path('tramite/vista/<int:numero_tramite>/', views.vista, name='vista'),
    path('tramite/editar/<int:numero_tramite>/', views.editar_tramite, name='editar_tramite'),
    path('tramite/pdf/<int:numero_tramite>/', views.generar_pdf_tramite, name='tramite_pdf'),
]