from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from apps.tramite.forms import TramiteForm, DepositoForm, TramiteEvaluacionForm
from .models import Tramite, Deposito

# ==========================================
# 1. MIXINS DE SEGURIDAD (Reglas de Negocio)
# ==========================================

class CualquierRolRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Permite el acceso a Usuarios, Administradores y Super Administradores"""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.rol_usuario in ['usuario', 'administrador', 'super_administrador']

class AdminOrSuperAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Permite el acceso SOLO a Administradores y Super Administradores"""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.rol_usuario in ['administrador', 'super_administrador']

class SoloSuperAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Permite el acceso EXCLUSIVAMENTE al Super Administrador"""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.rol_usuario == 'super_administrador'


# ==========================================
# 2. VISTAS CRUD DE TRÁMITES
# ==========================================

# VER TODOS (Usuario, Admin, SuperAdmin)
class TramiteListView(CualquierRolRequiredMixin, ListView):
    model = Tramite
    template_name = 'tramite/lista.html'
    context_object_name = 'tramites'

# VER DETALLE (Usuario, Admin, SuperAdmin)
class TramiteDetailView(CualquierRolRequiredMixin, DetailView):
    model = Tramite
    template_name = 'tramite/detalle.html'
    context_object_name = 'tramite'

# CREAR (Solo Admin y SuperAdmin)
class TramiteCreateView(AdminOrSuperAdminRequiredMixin, CreateView):
    model = Tramite
    template_name = 'tramite/crear.html'
    form_class = TramiteForm
    success_url = reverse_lazy('tramite:tramite_lista')

# tramites/views.py

class TramiteUpdateView(CualquierRolRequiredMixin, UpdateView):
    model = Tramite
    template_name = 'tramite/editar.html'
    success_url = reverse_lazy('tramite:tramite_lista')

    # ELIMINAMOS la línea "form_class = TramiteForm" y usamos esta función dinámica:
    def get_form_class(self):
        # Si el que inició sesión es el evaluador (rol 'usuario'):
        if self.request.user.rol_usuario == 'usuario':
            return TramiteEvaluacionForm
            
        # Si es 'administrador' o 'super_administrador', le damos el poder total:
        return TramiteForm

    # EXTRA PRO: Guardar automáticamente la fecha de validación/observación
    def form_valid(self, form):
        from django.utils import timezone
        
        tramite = form.save(commit=False)
        # Si cambió el estado a validado, registramos la hora exacta
        if tramite.estado_tramite == 'validado' and not tramite.fecha_validacion:
            tramite.fecha_validacion = timezone.now()
        # Si lo observó, registramos la hora exacta
        elif tramite.estado_tramite == 'observado' and not tramite.fecha_observacion:
            tramite.fecha_observacion = timezone.now()
            
        tramite.save()
        return super().form_valid(form)

# ELIMINAR (Solo SuperAdmin)
class TramiteDeleteView(SoloSuperAdminRequiredMixin, DeleteView):
    model = Tramite
    template_name = 'tramite/eliminar.html'
    success_url = reverse_lazy('tramite:tramite_lista')

# ==========================================
# 3. VISTAS CRUD DE DEPÓSITOS
# ==========================================

# VER TODOS LOS DEPÓSITOS (Solo Admin y SuperAdmin - Para control contable)
class DepositoListView(AdminOrSuperAdminRequiredMixin, ListView):
    model = Deposito
    template_name = 'tramite/deposito_lista.html'
    context_object_name = 'depositos'

# CREAR DEPÓSITO (Solo Admin y SuperAdmin)
class DepositoCreateView(AdminOrSuperAdminRequiredMixin, CreateView):
    model = Deposito
    form_class = DepositoForm
    template_name = 'tramite/deposito_crear.html'
    
    # Truco pro: Si venimos desde la vista de un trámite, pre-seleccionamos el trámite
    def get_initial(self):
        initial = super().get_initial()
        if 'tramite_id' in self.kwargs:
            initial['tramite'] = self.kwargs['tramite_id']
        return initial

    def get_success_url(self):
        # Al guardar, devolvemos al usuario al detalle del trámite al que le hizo el depósito
        return reverse_lazy('tramite:tramite_detalle', kwargs={'pk': self.object.tramite.id})

# EDITAR DEPÓSITO (Solo Admin y SuperAdmin)
class DepositoUpdateView(AdminOrSuperAdminRequiredMixin, UpdateView):
    model = Deposito
    form_class = DepositoForm
    template_name = 'tramite/deposito_editar.html'

    def get_success_url(self):
        return reverse_lazy('tramite:tramite_detalle', kwargs={'pk': self.object.tramite.id})

# ELIMINAR DEPÓSITO (Solo SuperAdmin)
class DepositoDeleteView(SoloSuperAdminRequiredMixin, DeleteView):
    model = Deposito
    template_name = 'tramite/deposito_eliminar.html'
    
    def get_success_url(self):
        # Al eliminar, devolvemos a la lista general de trámites
        return reverse_lazy('tramite:tramite_lista')