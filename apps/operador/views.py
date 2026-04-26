import logging
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpRequest
from django.template.loader import get_template
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.contrib import messages
from django.db import DatabaseError
from xhtml2pdf import pisa

from .models import Operador
from .forms import NuevoOperadorForm, FederacionForm, OrganizacionForm
from apps.afiliado.forms import NuevoAfiliadoForm
from apps.tramite.models import Tramite

logger = logging.getLogger(__name__)

def lista_operadores(request: HttpRequest) -> HttpResponse:
    q = request.GET.get('q', '').strip()
    
    try:
        operadores_list = Operador.objects.select_related('organizacion', 'federacion').all().order_by('-fecha_registro')
        
        if q:
            filtros = Q(organizacion__nombre__icontains=q) | Q(federacion__nombre__icontains=q)
            operadores_list = operadores_list.filter(filtros)
            
        paginator = Paginator(operadores_list, 5) 
        page_number = request.GET.get('page')
        operadores = paginator.get_page(page_number)
        
    except DatabaseError as e:
        logger.error(f"Error de base de datos en lista_operadores: {e}")
        messages.error(request, "Ocurrió un error al cargar la lista de operadores.")
        operadores = []

    form_operador = NuevoOperadorForm()
    form_organizacion = OrganizacionForm()
    form_federacion = FederacionForm()
    
    if request.method == 'POST':
        try:
            if 'submit_operador' in request.POST:
                form_operador = NuevoOperadorForm(request.POST)
                if form_operador.is_valid():
                    form_operador.save()
                    messages.success(request, "Operador registrado exitosamente.")
                    return redirect('operador:lista_operadores')
                    
            elif 'submit_organizacion' in request.POST:
                form_organizacion = OrganizacionForm(request.POST)
                if form_organizacion.is_valid():
                    form_organizacion.save()
                    messages.success(request, "Organización registrada correctamente.")
                    return redirect('operador:lista_operadores')
                    
            elif 'submit_federacion' in request.POST:
                form_federacion = FederacionForm(request.POST)
                if form_federacion.is_valid():
                    form_federacion.save()
                    messages.success(request, "Federación registrada correctamente.")
                    return redirect('operador:lista_operadores')
                    
        except Exception as e:
            logger.error(f"Error procesando formulario en lista_operadores: {e}")
            messages.error(request, "Error inesperado al intentar guardar los datos.")
            
    contexto = {
        'operadores': operadores,
        'q': q,
        'form_operador': form_operador,
        'form_organizacion': form_organizacion,
        'form_federacion': form_federacion,
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'operador/parcial_tabla.html', contexto)

    return render(request, 'operador/lista.html', contexto)
    
def detalle_operador(request: HttpRequest, id_operador: int) -> HttpResponse:
    operador = get_object_or_404(
        Operador.objects.select_related('organizacion', 'federacion'), 
        id=id_operador
    )
    
    form_operador = NuevoOperadorForm(instance=operador)
    form_afiliado = NuevoAfiliadoForm()

    if request.method == 'POST':
        try:
            if 'submit_operador' in request.POST:
                form_operador = NuevoOperadorForm(request.POST, instance=operador)
                if form_operador.is_valid():
                    form_operador.save()
                    messages.success(request, "Datos del operador actualizados.")
                    return redirect('operador:detalle_operador', id_operador=operador.id)
                    
            elif 'submit_afiliado' in request.POST:
                form_afiliado = NuevoAfiliadoForm(request.POST)
                if form_afiliado.is_valid():
                    nuevo_afiliado = form_afiliado.save(commit=False)
                    nuevo_afiliado.operador = operador 
                    nuevo_afiliado.save()
                    messages.success(request, "Afiliado vinculado correctamente.")
                    return redirect('operador:detalle_operador', id_operador=operador.id)
                    
        except Exception as e:
            logger.error(f"Error procesando formularios en detalle_operador {id_operador}: {e}")
            messages.error(request, "Error interno al intentar guardar los cambios.")

    contexto = {
        'operador': operador,
        'form_operador': form_operador,
        'form_afiliado': form_afiliado,
    }
    return render(request, 'operador/detalle.html', contexto)

def descargar_reporte_operador_pdf(request: HttpRequest, operador_id: int) -> HttpResponse:
    operador = get_object_or_404(Operador, id=operador_id)

    try:
        total_afiliados = operador.afiliado_operador.count()
        
        totales_tarjetas = operador.tarjeta_operador.aggregate(
            total_cantidad=Count('id'),
            total_monto=Sum('monto')
        )

        afiliados = operador.afiliado_operador.annotate(
            num_tarjetas=Count('tarjeta_afiliado', distinct=True),
            aporte_total=Sum('tarjeta_afiliado__monto'),
            num_vehiculos=Count('vehiculo_afiliado', distinct=True)
        ).prefetch_related(
            'vehiculo_afiliado__tipo', 
            'vehiculo_afiliado__marca'
        )

        tarjetas_por_tramite_raw = operador.tarjeta_operador.values(
            'tramite__tipo', 
            'tramite__estado'
        ).annotate(
            cantidad=Count('id')
        ).order_by('-cantidad')

        TIPO_DICT = dict(Tramite.TIPO)
        ESTADO_DICT = dict(Tramite.ESTADO)
        
        tarjetas_por_tramite = [
            {
                'tipo': TIPO_DICT.get(t['tramite__tipo'], 'Desconocido'),
                'estado': ESTADO_DICT.get(t['tramite__estado'], 'Desconocido'),
                'cantidad': t['cantidad']
            }
            for t in tarjetas_por_tramite_raw
        ]

        ingresos_mensuales = operador.tarjeta_operador.filter(
            fecha_emision__isnull=False
        ).annotate(
            mes=TruncMonth('fecha_emision')
        ).values('mes').annotate(
            cantidad_tarjetas=Count('id'),
            monto_generado=Sum('monto')
        ).order_by('-mes')

        hoy = timezone.localdate()
        limite = hoy + timedelta(days=30)
        
        tarjetas_por_vencer = operador.tarjeta_operador.filter(
            valida_hasta__lte=limite 
        ).select_related('afiliado', 'vehiculo').order_by('valida_hasta')

        context = {
            'operador': operador,
            'fecha_reporte': timezone.now(),
            'total_afiliados': total_afiliados,
            'totales_tarjetas': totales_tarjetas,
            'afiliados': afiliados,
            'tarjetas_por_tramite': tarjetas_por_tramite,
            'ingresos_mensuales': ingresos_mensuales,
            'tarjetas_por_vencer': tarjetas_por_vencer,
        }

        template = get_template('reportes/reporte_operador.html')
        html = template.render(context)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Reporte_{operador.organizacion.nombre}.pdf"'

        pisa_status = pisa.CreatePDF(html.encode('utf-8'), dest=response)

        if pisa_status.err:
            logger.error(f"Error de Pisa al generar PDF de operador {operador_id}: {pisa_status.err}")
            messages.error(request, "El motor de PDF falló al intentar renderizar el documento.")
            return redirect('operador:detalle_operador', id_operador=operador.id)
        
        return response
        
    except Exception as e:
        logger.error(f"Error crítico al generar reporte PDF para operador {operador_id}: {e}")
        messages.error(request, "Error interno al recuperar los datos para generar el PDF.")
        return redirect('operador:detalle_operador', id_operador=operador.id)