from django.urls import path, include
from . import views

app_name = 'tramite'

urlpatterns = [
    path('tramites/', views.lista_tramites, name='lista_tramites'),
    path('tramite/nuevo/', views.crear_tramite, name='crear_tramite'),
    path('tramite/<int:numero_tramite>/', views.detalle_tramite, name='detalle_tramite'),



    # path('tramites/<int:pk>/editar/', views.TramiteUpdateView.as_view(), name='tramite_editar'),
    path('tramites/<int:pk>/eliminar/', views.TramiteDeleteView.as_view(), name='tramite_eliminar'),

    path('tramites/<int:pk>/', include(('apps.tarjeta_de_operacion.urls', 'tarjeta'), namespace='tarjetas')),

    # ==========================================
    # RUTAS PARA DEPÓSITOS
    # ==========================================
    path('depositos/', views.DepositoListView.as_view(), name='deposito_lista'),
    
    # Esta ruta es especial: Pasa el ID del trámite por la URL para amarrar el depósito
    path('tramites/<int:tramite_id>/deposito/nuevo/', views.DepositoCreateView.as_view(), name='deposito_crear'),
    
    path('depositos/<int:pk>/editar/', views.DepositoUpdateView.as_view(), name='deposito_editar'),
    path('depositos/<int:pk>/eliminar/', views.DepositoDeleteView.as_view(), name='deposito_eliminar'),
]