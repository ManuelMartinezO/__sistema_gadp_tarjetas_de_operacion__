from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logup/', views.logup_view, name='logup'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    
    
    path('usuarios/', views.UsuarioListView.as_view(), name='usuario_lista'),
    # path('usuarios/crear/', views.UsuarioCreateView.as_view(), name='usuario_crear'),
    path('usuarios/<int:pk>/', views.UsuarioDetailView.as_view(), name='usuario_detalle'),
    path('usuarios/<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/eliminar/', views.UsuarioDeleteView.as_view(), name='usuario_eliminar'),
]