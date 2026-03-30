from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Usuario
from .forms import RegistroForm

class InicioView(TemplateView):
    template_name = 'usuario/inicio.html'
    # Solo con heredar de LoginRequiredMixin, Django enviará al usuario
    # al login si intenta entrar a '/' sin sesión iniciada.

# ==========================================
# 1. MIXIN DE SEGURIDAD (Control de Roles)
# ==========================================
class SuperAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Verifica que el usuario haya iniciado sesión (LoginRequiredMixin)
    y que su rol sea 'super_administrador' (UserPassesTestMixin).
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.rol_usuario == 'super_administrador'
    
    # Si falla la prueba, a dónde lo enviamos? (Ej: a la página de login)
    login_url = '/login/' 

# ==========================================
# 2. VISTAS DE AUTENTICACIÓN (Públicas)
# ==========================================
class IniciarSesionView(LoginView):
    template_name = 'usuario/login.html'
    redirect_authenticated_user = True # Si ya está logueado, no lo deja ver el login

class CerrarSesionView(LogoutView):
    next_page = 'login' # A dónde va después de cerrar sesión

class RegistroUsuarioView(CreateView):
    """Vista para el 'Logup' público. Cualquiera puede registrarse aquí."""
    model = Usuario
    form_class = RegistroForm
    template_name = 'usuario/registro.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        # Aseguramos que quien se registre por aquí sea solo 'usuario' normal
        user = form.save(commit=False)
        user.rol_usuario = 'usuario'
        user.save()
        return super().form_valid(form)

# ==========================================
# 3. VISTAS CRUD (Protegidas: Solo SuperAdmin)
# ==========================================
class UsuarioListView(SuperAdminRequiredMixin, ListView):
    model = Usuario
    template_name = 'usuario/lista.html'
    context_object_name = 'usuarios' # Así llamaremos a la lista en el HTML

class UsuarioDetailView(SuperAdminRequiredMixin, DetailView):
    model = Usuario
    template_name = 'usuario/detalle.html'
    context_object_name = 'usuario'

class UsuarioCreateView(SuperAdminRequiredMixin, CreateView):
    model = Usuario
    form_class = RegistroForm # Usamos el mismo form para que encripte la clave
    template_name = 'usuario/crear.html'
    success_url = reverse_lazy('usuario_lista')

class UsuarioUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Usuario
    # Al editar, permitimos cambiar casi todo (la clave se cambia en otra vista por seguridad)
    fields = ['username', 'email', 'nombre', 'apellido', 'numero_carnet_ci', 'numero_celular', 'rol_usuario', 'is_active']
    template_name = 'usuario/editar.html'
    success_url = reverse_lazy('usuario_lista')

class UsuarioDeleteView(SuperAdminRequiredMixin, DeleteView):
    model = Usuario
    template_name = 'usuario/eliminar.html'
    success_url = reverse_lazy('usuario_lista')
