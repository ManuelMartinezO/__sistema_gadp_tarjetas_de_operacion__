from django.urls import path
from . import views

app_name = 'tramite'

urlpatterns = [
    # ==========================================
    # RUTAS PARA TRÁMITES
    # ==========================================
    path('tramites/', views.TramiteListView.as_view(), name='tramite_lista'),
    path('tramites/nuevo/', views.TramiteCreateView.as_view(), name='tramite_crear'),
    path('tramites/<int:pk>/', views.TramiteDetailView.as_view(), name='tramite_detalle'),
    path('tramites/<int:pk>/editar/', views.TramiteUpdateView.as_view(), name='tramite_editar'),
    path('tramites/<int:pk>/eliminar/', views.TramiteDeleteView.as_view(), name='tramite_eliminar'),

    # ==========================================
    # RUTAS PARA DEPÓSITOS
    # ==========================================
    path('depositos/', views.DepositoListView.as_view(), name='deposito_lista'),
    
    # Esta ruta es especial: Pasa el ID del trámite por la URL para amarrar el depósito
    path('tramites/<int:tramite_id>/deposito/nuevo/', views.DepositoCreateView.as_view(), name='deposito_crear'),
    
    path('depositos/<int:pk>/editar/', views.DepositoUpdateView.as_view(), name='deposito_editar'),
    path('depositos/<int:pk>/eliminar/', views.DepositoDeleteView.as_view(), name='deposito_eliminar'),
]