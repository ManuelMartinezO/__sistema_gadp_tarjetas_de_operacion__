import io
import qrcode
import base64
import logging
from dateutil.relativedelta import relativedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import get_template
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib import messages
from django.db import transaction, DatabaseError
from xhtml2pdf import pisa

from django.contrib.auth.decorators import login_required, user_passes_test
from apps.usuario.permisos import es_admin, es_superadmin, es_usuario_normal

from .models import TarjetaDeOperacion
from .forms import TarjetaDeOperacionForm
from apps.tramite.models import Tramite

logger = logging.getLogger(__name__)

@login_required
@user_passes_test(es_admin, login_url='/', redirect_field_name=None)
def lista_tarjetas(request: HttpRequest) -> HttpResponse:
    # 1. Capturamos los términos de búsqueda
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', 'todos')

    try:
        # 2. Eliminamos 'ruta' del select_related
        tarjetas_list = TarjetaDeOperacion.objects.select_related(
            'vehiculo', 
            'afiliado', 
            'operador__organizacion', # Viajamos a la relación anidada
            'operador__federacion',   # Viajamos a la relación anidada
            'tramite'
        ).all().order_by('-id')

        # 3. Filtro dinámico: Placa, Afiliado (nombre/apellido) o Sindicato (operador)
        if q:
            filtros_q = (
                Q(vehiculo__placa__icontains=q) |
                Q(afiliado__nombre_completo__icontains=q) |          # Ajustado al Afiliado
                Q(operador__organizacion__nombre__icontains=q) |     # Búsqueda en la Organización
                Q(operador__federacion__nombre__icontains=q)         # Búsqueda en la Federación
            )
            if q.isdigit():
                filtros_q |= Q(id=q)
            tarjetas_list = tarjetas_list.filter(filtros_q)

        # 4. Filtro por Estado
        if estado != 'todos':
            if estado == 'emitida':
                tarjetas_list = tarjetas_list.filter(fecha_emision__isnull=False)
            elif estado == 'pendiente':
                tarjetas_list = tarjetas_list.filter(fecha_emision__isnull=True)

        # 5. Paginación
        paginator = Paginator(tarjetas_list, 10)
        page_number = request.GET.get('page')
        tarjetas = paginator.get_page(page_number)

    except DatabaseError as e:
        logger.error(f"Error de base de datos en lista_tarjetas: {e}")
        messages.error(request, "Ocurrió un error al cargar el listado.")
        tarjetas = []

    contexto = {
        'tarjetas': tarjetas,
        'q': q,
        'estado_actual': estado,
    }
    
    # 6. Respuesta para AJAX (búsqueda en tiempo real)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'tarjeta/parcial_tabla.html', contexto)

    # 7. Respuesta estándar
    return render(request, 'tarjeta/lista.html', contexto)

@login_required
@user_passes_test(es_admin, login_url='/', redirect_field_name=None)
@transaction.atomic
def generar_pdf_tarjeta(request: HttpRequest, id_tarjeta: int) -> HttpResponse:
    tarjeta = get_object_or_404(TarjetaDeOperacion, id=id_tarjeta)
    
    try:
        if tarjeta.estado == 'p':
            fecha_actual = timezone.now().date()
            
            # 1. Obtenemos todas las tarjetas asociadas al MISMO TRÁMITE que estén pendientes ('p').
            # REEMPLAZA 'tramite' por el nombre del campo o relación correcta en tu modelo.
            tarjetas_pendientes = TarjetaDeOperacion.objects.filter(
                tramite=tarjeta.tramite, 
                estado='p'
            )
            
            tarjetas_a_actualizar = []
            
            # 2. Asignamos las nuevas fechas y estados a cada tarjeta relacionada
            for t in tarjetas_pendientes:
                t.fecha_emision = fecha_actual
                t.valida_hasta = fecha_actual + relativedelta(years=t.validez)
                t.estado = 'e'
                tarjetas_a_actualizar.append(t)
            
            # 3. Guardamos los cambios de todas las tarjetas en la base de datos de una sola vez
            if tarjetas_a_actualizar:
                with transaction.atomic():
                    TarjetaDeOperacion.objects.bulk_update(
                        tarjetas_a_actualizar, 
                        ['fecha_emision', 'valida_hasta', 'estado']
                    )
            
            # 4. Refrescamos la instancia actual desde la BD para asegurar que el código QR 
            # tome las fechas actualizadas generadas en el bloque anterior.
            tarjeta.refresh_from_db()

        texto_qr = (
            f"PLACA: {tarjeta.vehiculo.placa}\n"
            f"MARCA: {tarjeta.vehiculo.marca}\n"
            f"MODELO: {tarjeta.vehiculo.modelo}\n"
            f"ESTADO: {tarjeta.get_estado_display()}\n"
            f"VENCE: {tarjeta.valida_hasta}\n"
        )
        
        qr = qrcode.QRCode(
            version=1,  
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(texto_qr)
        qr.make(fit=True)
        
        buffer = io.BytesIO()
        img_qr = qr.make_image(fill_color="black", back_color="white")
        img_qr.save(buffer, format='PNG')
        imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        qr_data_uri = f"data:image/png;base64,{imagen_base64}"
        
        contexto = {
            'tarjeta': tarjeta,
            'qr_data_uri': qr_data_uri,
        }
        
        template = get_template('pdf/tarjeta.html')
        template_render = template.render(contexto)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Tarjeta_Vehiculo_{tarjeta.vehiculo.placa}.pdf"'
        
        pisa_status = pisa.CreatePDF(template_render, dest=response)
        
        if pisa_status.err:
            logger.error(f"Error generando PDF para tarjeta {id_tarjeta}: {pisa_status.err}")
            messages.error(request, "El motor de PDF falló al intentar renderizar la tarjeta.")
            # Redirigir a una ruta segura en caso de fallo (ajusta la URL según tu app)
            return redirect('tarjeta:lista_tarjetas')
            
        return response
        
    except Exception as e:
        logger.error(f"Error procesando la tarjeta de operación {id_tarjeta}: {e}")
        messages.error(request, "Error interno al intentar generar el documento.")
        return redirect('tarjeta:lista_tarjetas')

@login_required
@user_passes_test(es_admin, login_url='/', redirect_field_name=None)
@transaction.atomic
def imprimir_todas_tarjetas(request: HttpRequest, id_tramite: int) -> HttpResponse:
    # 1. Obtenemos el trámite correspondiente
    tramite = get_object_or_404(Tramite, id=id_tramite)
    
    try:
        # 2. Recuperamos todas las tarjetas asociadas al trámite
        tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).select_related(
            'vehiculo', 'afiliado', 'operador__organizacion', 'operador__federacion', 'tramite'
        ).order_by('id')

        if not tarjetas.exists():
            messages.error(request, "No existen tarjetas registradas en este trámite para imprimir.")
            return redirect('tramite:lista_tramites')

        # 3. Activación masiva si existen tarjetas pendientes ('p') dentro del lote
        tarjetas_pendientes = [t for t in tarjetas if t.estado == 'p']
        if tarjetas_pendientes:
            fecha_actual = timezone.now().date()
            tarjetas_a_actualizar = []
            
            for t in tarjetas_pendientes:
                t.fecha_emision = fecha_actual
                t.valida_hasta = fecha_actual + relativedelta(years=t.validez)
                t.estado = 'e'
                tarjetas_a_actualizar.append(t)
                
            TarjetaDeOperacion.objects.bulk_update(
                tarjetas_a_actualizar, 
                ['fecha_emision', 'valida_hasta', 'estado']
            )
            # Refrescamos la consulta para asegurar que los datos actualizados vayan al QR
            tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).select_related(
                'vehiculo', 'afiliado', 'operador__organizacion', 'operador__federacion', 'tramite'
            ).order_by('id')

        # 4. Generación iterativa de códigos QR para cada tarjeta
        for tarjeta in tarjetas:
            texto_qr = (
                f"PLACA: {tarjeta.vehiculo.placa}\n"
                f"MARCA: {tarjeta.vehiculo.marca.nombre}\n"
                f"MODELO: {tarjeta.vehiculo.modelo}\n"
                f"ESTADO: {tarjeta.get_estado_display()}\n"
                f"EMITIDA: {tarjeta.fecha_emision}\n"
                f"VENCE: {tarjeta.valida_hasta}\n"
            )
            
            qr = qrcode.QRCode(
                version=1,  
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(texto_qr)
            qr.make(fit=True)
            
            buffer = io.BytesIO()
            img_qr = qr.make_image(fill_color="black", back_color="white")
            img_qr.save(buffer, format='PNG')
            imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Acoplamos el URI de la imagen como atributo dinámico a cada objeto tarjeta
            tarjeta.qr_data_uri = f"data:image/png;base64,{imagen_base64}"

        # 5. Pasamos la colección completa al contexto de la plantilla masiva
        contexto = {
            'tramite': tramite,
            'tarjetas': tarjetas,
        }
        
        template = get_template('pdf/todas_tarjetas.html')
        template_render = template.render(contexto)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Tarjetas_Tramite_{tramite.numero}.pdf"'
        
        pisa_status = pisa.CreatePDF(template_render, dest=response)
        
        if pisa_status.err:
            logger.error(f"Error generando PDF por lote para el trámite {id_tramite}: {pisa_status.err}")
            messages.error(request, "El motor de renderizado falló al compilar el lote de tarjetas.")
            return redirect('tramite:lista_tramites')
            
        return response
        
    except Exception as e:
        logger.error(f"Error procesando lote de tarjetas del trámite {id_tramite}: {e}")
        messages.error(request, "Error interno al intentar generar el documento unificado.")
        return redirect('tramite:lista_tramites')

@login_required
@user_passes_test(es_admin, login_url='/', redirect_field_name=None)
def detalle_tarjeta(request: HttpRequest, id_tarjeta: int) -> HttpResponse:
    # Usamos select_related para optimizar la carga de relaciones foráneas
    tarjeta = get_object_or_404(
        TarjetaDeOperacion.objects.select_related(
            'vehiculo', 'afiliado', 'operador', 'tramite'
        ),
        id=id_tarjeta
    )
    
    contexto = {
        'tarjeta': tarjeta,
    }
    
    return render(request, 'tarjeta/detalle.html', contexto)

@login_required
@user_passes_test(es_admin, login_url='/', redirect_field_name=None)
def editar_tarjeta(request: HttpRequest, id_tarjeta: int) -> HttpResponse:
    tarjeta = get_object_or_404(TarjetaDeOperacion, id=id_tarjeta)
    
    if request.method == 'POST':
        # Pasamos request.POST y la instancia que queremos actualizar
        form = TarjetaDeOperacionForm(request.POST, request.FILES, instance=tarjeta)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"La tarjeta {tarjeta.id} se actualizó correctamente.")
                # Redirigimos al detalle de la tarjeta recién editada
                return redirect('tarjeta:detalle_tarjeta', id_tarjeta=tarjeta.id)
            except DatabaseError as e:
                logger.error(f"Error de base de datos al actualizar la tarjeta {id_tarjeta}: {e}")
                messages.error(request, "Ocurrió un error interno al intentar guardar los cambios.")
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        form = TarjetaDeOperacionForm(instance=tarjeta)
        
    contexto = {
        'form': form,
        'tarjeta': tarjeta,
    }
    
    return render(request, 'tarjeta/editar.html', contexto)