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
    q = request.GET.get('q', '').strip()
    ruta_q = request.GET.get('ruta', '').strip()
    tipo = request.GET.get('tipo', 'todos')
    estado = request.GET.get('estado', 'todos')

    try:
        tarjetas_list = TarjetaDeOperacion.objects.select_related(
            'vehiculo', 'afiliado', 'operador', 'ruta', 'tramite'
        ).all().order_by('-id')

        if q:
            filtros_q = (
                Q(vehiculo__placa__icontains=q) |
                Q(afiliado__nombre__icontains=q) |
                Q(afiliado__apellido__icontains=q) |
                Q(operador__nombre__icontains=q)
            )
            if q.isdigit():
                filtros_q |= Q(id=q)
            tarjetas_list = tarjetas_list.filter(filtros_q)

        if ruta_q:
            tarjetas_list = tarjetas_list.filter(ruta__ruta__icontains=ruta_q)

        if tipo and tipo != 'todos':
            tarjetas_list = tarjetas_list.filter(tipo_tarjeta=tipo)

        if estado != 'todos':
            if estado == 'emitida':
                tarjetas_list = tarjetas_list.filter(fecha_emision__isnull=False)
            elif estado == 'pendiente':
                tarjetas_list = tarjetas_list.filter(fecha_emision__isnull=True)

        paginator = Paginator(tarjetas_list, 5)
        page_number = request.GET.get('page')
        tarjetas = paginator.get_page(page_number)

    except DatabaseError as e:
        logger.error(f"Error de base de datos en lista_tarjetas: {e}")
        messages.error(request, "Ocurrió un error al cargar el listado de tarjetas.")
        tarjetas = []

    contexto = {
        'tarjetas': tarjetas,
        'q': q,
        'ruta_q': ruta_q,
        'tipo_actual': tipo,
        'estado_actual': estado,
        'tipos_tarjeta': getattr(TarjetaDeOperacion, 'TIPO_TARJETA', []),
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'tarjeta/parcial_tabla.html', contexto)

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