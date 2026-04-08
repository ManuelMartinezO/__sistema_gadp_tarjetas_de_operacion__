from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from apps.tramite.forms import TramiteEviadoForm, TramiteReportadoForm, DepositoForm
from django.shortcuts import render, get_object_or_404, redirect
from .models import Tramite, Deposito
from apps.tarjeta_de_operacion.forms import TarjetaDeOperacionForm
from apps.vehiculo.forms import VehiculoForm
from apps.afiliado.forms import AfiliadoForm
from apps.operador.forms import OperadorForm
from apps.tarjeta_de_operacion.models import TarjetaDeOperacion

import qrcode
import io
import base64
from django.template.loader import get_template
from django.http import HttpResponse, JsonResponse
from xhtml2pdf import pisa


# === TRAMITE VIEWS ===
def lista_tramites (request):
    tramites = Tramite.objects.all()
    contexto = {
        'tramites': tramites,
    }
    return render(request, 'tramite/lista.html', contexto)

def detalle_tramite (request, numero_tramite):
    tramite = get_object_or_404(Tramite, numero_tramite=numero_tramite)
    tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).order_by('-fecha_registro')
    if request.method == 'POST':
        if 'btn_reporte' in request.POST:
            form_reporte = TramiteReportadoForm(request.POST, request.FILES, instance=tramite, prefix='reporte')
            if form_reporte.is_valid():
                guardado = form_reporte.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
        if 'btn_tarjeta' in request.POST:
            form_tarjeta = TarjetaDeOperacionForm(request.POST, prefix='tarjeta')
            if form_tarjeta.is_valid():
                tarjeta_guardado = form_tarjeta.save(commit=False)
                tarjeta_guardado.tramite = tramite
                tarjeta_guardado.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
        if 'btn_deposito' in request.POST:
            form_deposito = DepositoForm(request.POST, prefix='deposito')
            if form_deposito.is_valid():
                deposito_guardado = form_deposito.save(commit=False)
                deposito_guardado.tramite = tramite
                tramite.estado_deposito = True
                tramite.save()
                deposito_guardado.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
    else:
        form_reporte = TramiteReportadoForm(prefix='reporte')
        form_tarjeta = TarjetaDeOperacionForm(prefix='tarjeta')
        form_deposito = DepositoForm(prefix='deposito')
    contexto = {
        'tramite': tramite,
        'tarjetas': tarjetas,
        'n_tarjetas': tarjetas.count(),
        'form_tarjeta': form_tarjeta,
        'form_reporte': form_reporte,
        'form_deposito': form_deposito,
    }
    return render(request, 'tramite/detalle.html', contexto)

def crear_tramite (request):
    if request.method == 'POST':
        form = TramiteEviadoForm(request.POST, request.FILES)
        if form.is_valid():
            guardado = form.save()
            return redirect('tramite:lista_tramites')
    else:
        form = TramiteEviadoForm()
    contexto = {
        'form': form
    }
    return render(request, 'tramite/crear.html', contexto)


def generar_pdf_tramite (request, numero_tramite):
    tramite = get_object_or_404(Tramite, numero_tramite=numero_tramite)
    tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).order_by('-fecha_registro')
    costo_total = sum(tarjeta.monto for tarjeta in tarjetas)
    for tarjeta in tarjetas:
        fecha_emision_str = tarjeta.fecha_emision.strftime('%d/%m/%Y') if tarjeta.fecha_emision else "Pendiente"
        valida_hasta_str = tarjeta.valida_hasta.strftime('%d/%m/%Y') if tarjeta.valida_hasta else "Pendiente"
        
        # Generar un texto estructurado y profesional para el escáner
        texto_qr = (
            "🏛️ G.A.D. POTOSI - SEC. TRANSPORTE\n"
            "----------------------------------\n"
            f"📄 TARJETA Nº: {tarjeta.id:06d}\n"
            f"🚗 PLACA: {tarjeta.vehiculo.placa}\n"
            f"🚙 VEHICULO: {tarjeta.vehiculo.marca.nombre} {tarjeta.vehiculo.modelo}\n"
            f"👤 TITULAR: {tarjeta.afiliado.nombre} {tarjeta.afiliado.apellido}\n"
            f"🏢 OPERADOR: {tarjeta.operador.nombre}\n"
            f"📌 SERVICIO: {tarjeta.get_tipo_tarjeta_display().upper()}\n"
            f"✅ EMISION: {fecha_emision_str}\n"
            f"⛔ VENCE: {valida_hasta_str}\n"
            "----------------------------------\n"
            f"🔍 Ref. Trámite: {tramite.numero_tramite}"
        )
        qr = qrcode.QRCode(
            version=1,  
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(texto_qr)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img_qr.save(buffer, format='PNG')
        imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        tarjeta.qr_data_uri = f"data:image/png;base64,{imagen_base64}"
        
    contexto = {
        'tramite': tramite,
        'tarjetas': tarjetas,
        'costo_total': costo_total,
    }
    template = get_template('pdf/tramite.html')
    template_render = template.render(contexto)
    response = HttpResponse(content_type = 'application/pdf')
    response['Content-Disposition'] = f'inline; filename="Tramite_{tramite.numero_tramite}.pdf"'
    pisa_status = pisa.CreatePDF(template_render, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF')
    return response








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
# class TramiteCreateView(AdminOrSuperAdminRequiredMixin, CreateView):
#     model = Tramite
#     template_name = 'tramite/crear.html'
#     form_class = TramiteForm
#     success_url = reverse_lazy('tramite:tramite_lista')

# tramites/views.py

# class TramiteUpdateView(CualquierRolRequiredMixin, UpdateView):
#     model = Tramite
#     template_name = 'tramite/editar.html'
#     success_url = reverse_lazy('tramite:tramite_lista')

#     # ELIMINAMOS la línea "form_class = TramiteForm" y usamos esta función dinámica:
#     def get_form_class(self):
#         # Si el que inició sesión es el evaluador (rol 'usuario'):
#         if self.request.user.rol_usuario == 'usuario':
#             return TramiteEvaluacionForm
            
#         # Si es 'administrador' o 'super_administrador', le damos el poder total:
#         return TramiteForm

#     # EXTRA PRO: Guardar automáticamente la fecha de validación/observación
#     def form_valid(self, form):
#         from django.utils import timezone
        
#         tramite = form.save(commit=False)
#         # Si cambió el estado a validado, registramos la hora exacta
#         if tramite.estado_tramite == 'validado' and not tramite.fecha_validacion:
#             tramite.fecha_validacion = timezone.now()
#         # Si lo observó, registramos la hora exacta
#         elif tramite.estado_tramite == 'observado' and not tramite.fecha_observacion:
#             tramite.fecha_observacion = timezone.now()
            
#         tramite.save()
#         return super().form_valid(form)

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