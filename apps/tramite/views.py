from .models import Tramite
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from apps.tramite.forms import TramiteEviadoForm, TramiteReportadoForm, DepositoForm, EditarTramiteForm, EditarInformeForm, EditarEstadoForm, EditarReporteForm
from apps.usuario.permisos import es_admin, es_superadmin, es_usuario_normal
from django.template.loader import get_template
from apps.tarjeta_de_operacion.forms import TarjetaDeOperacionForm
from apps.tarjeta_de_operacion.models import TarjetaDeOperacion
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.utils.dateparse import parse_date

import qrcode
import io
import base64

# ========== TRAMITE VIEWS ==========
@login_required()
@user_passes_test(es_usuario_normal)
def lista_tramites(request):
    # Por defecto, obtenemos todos y los ordenamos por los más recientes
    tramites = Tramite.objects.all().order_by('-fecha_registro')

    # 1. Obtener los parámetros de búsqueda del frontend
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', 'todos')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    tipo = request.GET.get('tipo', 'todos')

    # 2. Filtrar por coincidencia de texto (Input)
    if q:
        # Buscamos por usuario
        filtros = Q(usuario__username__icontains=q)
        # Si el usuario ingresó solo números, también buscamos por N° de trámite
        if q.isdigit():
            filtros |= Q(numero_tramite__icontains=q)
        
        tramites = tramites.filter(filtros)

    # 3. Filtrar por Estado (Validado, Pendiente, Observado)
    if estado and estado != 'todos':
        tramites = tramites.filter(estado_tramite=estado)

    # Filtro por Tipo <-- Nueva lógica
    if tipo and tipo != 'todos':
        tramites = tramites.filter(tipo_tramite=tipo)

    # 4. Filtrar por Rango de Fechas
    if fecha_inicio:
        tramites = tramites.filter(fecha_registro__date__gte=parse_date(fecha_inicio))
    if fecha_fin:
        tramites = tramites.filter(fecha_registro__date__lte=parse_date(fecha_fin))

    # 5. Pasamos los filtros de vuelta al contexto para que los inputs no se borren al recargar
    contexto = {
        'tramites': tramites,
        'q': q,
        'estado_actual': estado,
        'tipo_actual': tipo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'tramite/lista.html', contexto)

@login_required()
@user_passes_test(es_usuario_normal)
def detalle_tramite (request, numero_tramite):
    tramite = get_object_or_404(Tramite, numero_tramite=numero_tramite)
    tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).order_by('-fecha_registro')
    if request.method == 'POST':
        if 'btn_reporte' in request.POST:
            form_reporte = TramiteReportadoForm(request.POST, request.FILES, instance=tramite, prefix='reporte')
            if form_reporte.is_valid():
                guardado = form_reporte.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
        if 'btn_tarjeta' in request.POST and request.user.rol == 'a' or request.user.rol == 'sa':
            form_tarjeta = TarjetaDeOperacionForm(request.POST, prefix='tarjeta')
            if form_tarjeta.is_valid():
                tarjeta_guardado = form_tarjeta.save(commit=False)
                tarjeta_guardado.tramite = tramite
                tarjeta_guardado.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
        if 'btn_deposito' in request.POST and request.user.rol == 'a' or request.user.rol == 'sa':
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

@login_required()
@user_passes_test(es_admin)
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

@login_required()
@user_passes_test(es_usuario_normal)
def editar_tramite (request, numero_tramite):
    tramite = get_object_or_404(Tramite, numero_tramite=numero_tramite)
    if request.method == 'POST':
        if 'btn_tramite' in request.POST and es_admin:
            form_tramite = EditarTramiteForm(request.POST, instance=tramite, prefix='editar_tramite')
            if form_tramite.is_valid():
                guardado = form_tramite.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
        if 'btn_informe' in request.POST and es_admin:
            form_informe = EditarInformeForm(request.POST, instance=tramite, prefix='editar_informe')
            if form_informe.is_valid():
                guardado = form_informe.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
        if 'btn_reporte' in request.POST and es_usuario_normal:
            form_reporte = EditarReporteForm(request.POST, instance=tramite, prefix='editar_reporte')
            if form_reporte.is_valid():
                guardado = form_reporte.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
        if 'btn_estado' in request.POST and es_usuario_normal:
            form_estado = EditarEstadoForm(request.POST, instance=tramite, prefix='editar_estado')
            if form_estado.is_valid():
                guardado = form_estado.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
    else:
        form_tramite = EditarTramiteForm(prefix='editar_tramite')
        form_informe = EditarInformeForm(prefix='editar_informe')
        form_reporte = EditarReporteForm(prefix='editar_reporte')
        form_estado = EditarEstadoForm(prefix='editar_estado')
    contexto = {
        'tramite': tramite,
        'form_tramite': form_tramite,
        'form_informe': form_informe,
        'form_reporte': form_reporte,
        'form_estado': form_estado,
    }
    return render(request, 'tramite/editar.html', contexto)

# ========== GENERACION DE PDFs ===========
@login_required()
@user_passes_test(es_admin)
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