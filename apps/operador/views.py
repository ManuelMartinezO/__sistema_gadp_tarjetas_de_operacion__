from django.shortcuts import render, get_object_or_404, redirect
from .models import Operador
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template.loader import get_template
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from xhtml2pdf import pisa # Importamos la librería para el PDF
from .forms import OperadorForm

def lista_operadores(request):
    # Obtenemos todos los operadores ordenados
    operadores_list = Operador.objects.all().order_by('-fecha_registro')
    
    # 1. Capturar la búsqueda
    q = request.GET.get('q', '').strip()
    
    # 2. Filtrar si existe búsqueda
    if q:
        operadores_list = operadores_list.filter(nombre__icontains=q)
        
    # 3. Configurar Paginación
    # (operadores_list, cantidad_por_pagina)
    paginator = Paginator(operadores_list, 5) 
    
    # Obtener el número de página actual de la URL (ej: ?page=2)
    page_number = request.GET.get('page')
    
    # Obtener el objeto de página (esto maneja automáticamente errores de página no encontrada)
    operadores = paginator.get_page(page_number)
        
    contexto = {
        'operadores': operadores, # Ahora este objeto contiene los métodos .has_next, .has_previous, etc.
        'q': q,
    }
    return render(request, 'operador/lista.html', contexto)
    
def detalle_operador (request, id_operador):
    operador = get_object_or_404(Operador, id=id_operador)
    contexto = {
        'operador': operador,
    }
    return render(request, 'operador/detalle.html', contexto)

def crear_operador (request):
    if request.method == 'POST':
        form = OperadorForm(request.POST)
        if form.is_valid():
            guardado = form.save()
            return redirect('operador:lista_operadores')
    else:
        form = OperadorForm()
    contexto = {
        'form': form
    }
    return render(request, 'operador/crear.html', contexto)

def editar_operador (request, id_operador):
    operador = get_object_or_404(Operador, id=id_operador)
    if request.method == 'POST':
        form = OperadorForm(request.POST, instance=operador)
        if form.is_valid():
            guardado = form.save()
            return redirect('operador:detalle_operador', operador.id)
    else:
        form = OperadorForm()
    contexto = {
        'operador': operador,
        'form': form,
    }
    return render(request, 'operador/editar.html', contexto)

def descargar_reporte_operador_pdf(request, operador_id):
    # 1. Obtener el operador (retorna 404 si no existe)
    operador = get_object_or_404(Operador, id=operador_id)

    # 2. Cálculos generales
    total_afiliados = operador.afiliados.count()
    
    # CORRECCIÓN: Se usa exactamente el related_name 'operadores_tarjeta' sin '_set'
    totales_tarjetas = operador.operadores_tarjeta.aggregate(
        total_cantidad=Count('id'),
        total_monto=Sum('monto')
    )

    # 3. Padrón de Afiliados (Optimizado con prefetch_related)
    # CORRECCIÓN: Se cambia a 'afiliados_tarjeta' porque ese es el related_name en el modelo
    afiliados = operador.afiliados.annotate(
        num_tarjetas=Count('afiliados_tarjeta', distinct=True),
        aporte_total=Sum('afiliados_tarjeta__monto'),
        num_vehiculos=Count('vehiculo', distinct=True)
    ).prefetch_related(
        'vehiculo_set__tipo_vehiculo', 
        'vehiculo_set__marca'
    )

    # 4. Distribución por tipo de trámite
    # CORRECCIÓN: 'operadores_tarjeta' en lugar de 'tarjetadeoperacion_set'
    tarjetas_por_tramite = operador.operadores_tarjeta.values(
        'tramite__tipo_tramite', 
        'tramite__estado_tramite'
    ).annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')

    # 5. Ingresos por Mes
    # CORRECCIÓN: 'operadores_tarjeta'
    ingresos_mensuales = operador.operadores_tarjeta.filter(
        fecha_emision__isnull=False
    ).annotate(
        mes=TruncMonth('fecha_emision')
    ).values('mes').annotate(
        cantidad_tarjetas=Count('id'),
        monto_generado=Sum('monto')
    ).order_by('-mes')

    # 6. Alertas de Vencimiento (Próximos 30 días o ya vencidas)
    hoy = timezone.localdate()
    limite = hoy + timedelta(days=30)
    
    # CORRECCIÓN: 'operadores_tarjeta'
    tarjetas_por_vencer = operador.operadores_tarjeta.filter(
        valida_hasta__lte=limite 
    ).select_related('afiliado', 'vehiculo').order_by('valida_hasta')

    # 7. Empaquetar el contexto
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

    # 8. Renderizar el Template HTML
    template = get_template('reportes/reporte_operador.html')
    html = template.render(context)

    # 9. Crear la respuesta HTTP como PDF
    response = HttpResponse(content_type='application/pdf')
    
    # 'inline' hace que se abra en el visor del navegador
    response['Content-Disposition'] = f'inline; filename="Reporte_{operador.nombre}.pdf"'

    # 10. Generar el PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Hubo un error al generar el PDF: <pre>' + html + '</pre>')
    
    return response