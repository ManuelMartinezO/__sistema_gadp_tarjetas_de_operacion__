from django.urls import path
from . import views

urlpatterns = [
    path('', views.InicioView.as_view(), name='inicio'),
    
    # Autenticación
    path('login/', views.IniciarSesionView.as_view(), name='login'),
    path('logout/', views.CerrarSesionView.as_view(), name='logout'),
    path('registro/', views.RegistroUsuarioView.as_view(), name='registro'),

    # CRUD de Usuarios (Solo SuperAdmin)
    path('usuarios/', views.UsuarioListView.as_view(), name='usuario_lista'),
    path('usuarios/crear/', views.UsuarioCreateView.as_view(), name='usuario_crear'),
    path('usuarios/<int:pk>/', views.UsuarioDetailView.as_view(), name='usuario_detalle'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/eliminar/', views.UsuarioDeleteView.as_view(), name='usuario_eliminar'),
]