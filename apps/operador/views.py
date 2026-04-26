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
from .forms import NuevoOperadorForm, FederacionForm, OrganizacionForm
from django.db.models import Q
from apps.afiliado.forms import NuevoAfiliadoForm
from apps.tramite.models import Tramite

def lista_operadores(request):
    # 1. Optimizar consulta con select_related para las llaves foráneas
    operadores_list = Operador.objects.select_related('organizacion', 'federacion').all().order_by('-fecha_registro')
    
    # 2. Capturar la búsqueda
    q = request.GET.get('q', '').strip()
    
    # 3. Filtrar por nombre de Organización o Federación
    if q:
        filtros = Q(organizacion__nombre__icontains=q) | Q(federacion__nombre__icontains=q)
        operadores_list = operadores_list.filter(filtros)
        
    # 4. Configurar Paginación
    paginator = Paginator(operadores_list, 5) 
    page_number = request.GET.get('page')
    operadores = paginator.get_page(page_number)
    
    # 5. Instanciar los formularios vacíos
    form_operador = NuevoOperadorForm()
    form_organizacion = OrganizacionForm()
    form_federacion = FederacionForm()
    
    # 6. Procesar los formularios si es una petición POST
    if request.method == 'POST':
        if 'submit_operador' in request.POST:
            form_operador = NuevoOperadorForm(request.POST)
            if form_operador.is_valid():
                form_operador.save()
                return redirect('operador:lista_operadores')
                
        elif 'submit_organizacion' in request.POST:
            form_organizacion = OrganizacionForm(request.POST)
            if form_organizacion.is_valid():
                form_organizacion.save()
                return redirect('operador:lista_operadores')
                
        elif 'submit_federacion' in request.POST:
            form_federacion = FederacionForm(request.POST)
            if form_federacion.is_valid():
                form_federacion.save()
                return redirect('operador:lista_operadores')
        
    contexto = {
        'operadores': operadores,
        'q': q,
        'form_operador': form_operador,
        'form_organizacion': form_organizacion,
        'form_federacion': form_federacion,
    }
    
    # 7. Detectar si es una petición AJAX para el buscador
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'operador/parcial_tabla.html', contexto)

    return render(request, 'operador/lista.html', contexto)
    
def detalle_operador(request, id_operador):
    # Optimizamos consultas trayendo también la organización y federación
    operador = get_object_or_404(
        Operador.objects.select_related('organizacion', 'federacion'), 
        id=id_operador
    )
    
    # Instanciamos formularios
    form_operador = NuevoOperadorForm(instance=operador)
    form_afiliado = NuevoAfiliadoForm()

    if request.method == 'POST':
        # A) Procesar edición del Operador
        if 'submit_operador' in request.POST:
            form_operador = NuevoOperadorForm(request.POST, instance=operador)
            if form_operador.is_valid():
                form_operador.save()
                return redirect('operador:detalle_operador', id_operador=operador.id)
                
        # B) Procesar creación de nuevo Afiliado
        elif 'submit_afiliado' in request.POST:
            form_afiliado = NuevoAfiliadoForm(request.POST)
            if form_afiliado.is_valid():
                # Guardamos temporalmente sin enviar a la BD
                nuevo_afiliado = form_afiliado.save(commit=False)
                # Le asignamos el operador actual automáticamente
                nuevo_afiliado.operador = operador 
                # Ahora sí, guardamos en la BD
                nuevo_afiliado.save()
                return redirect('operador:detalle_operador', id_operador=operador.id)

    contexto = {
        'operador': operador,
        'form_operador': form_operador,
        'form_afiliado': form_afiliado,
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
    # 1. Obtener el operador
    operador = get_object_or_404(Operador, id=operador_id)

    # 2. Cálculos generales (usando 'afiliado_operador' y 'tarjeta_operador')
    total_afiliados = operador.afiliado_operador.count()
    
    totales_tarjetas = operador.tarjeta_operador.aggregate(
        total_cantidad=Count('id'),
        total_monto=Sum('monto')
    )

    # 3. Padrón de Afiliados
    afiliados = operador.afiliado_operador.annotate(
        num_tarjetas=Count('tarjeta_afiliado', distinct=True),
        aporte_total=Sum('tarjeta_afiliado__monto'),
        num_vehiculos=Count('vehiculo_afiliado', distinct=True)
    ).prefetch_related(
        'vehiculo_afiliado__tipo', 
        'vehiculo_afiliado__marca'
    )

    # 4. Distribución por tipo de trámite
    tarjetas_por_tramite_raw = operador.tarjeta_operador.values(
        'tramite__tipo', 
        'tramite__estado'
    ).annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')

    # Mapear los choices para que el PDF muestre el texto legible, no la letra
    TIPO_DICT = dict(Tramite.TIPO)
    ESTADO_DICT = dict(Tramite.ESTADO)
    
    tarjetas_por_tramite = []
    for t in tarjetas_por_tramite_raw:
        tarjetas_por_tramite.append({
            'tipo': TIPO_DICT.get(t['tramite__tipo'], 'Desconocido'),
            'estado': ESTADO_DICT.get(t['tramite__estado'], 'Desconocido'),
            'cantidad': t['cantidad']
        })

    # 5. Ingresos por Mes
    ingresos_mensuales = operador.tarjeta_operador.filter(
        fecha_emision__isnull=False
    ).annotate(
        mes=TruncMonth('fecha_emision')
    ).values('mes').annotate(
        cantidad_tarjetas=Count('id'),
        monto_generado=Sum('monto')
    ).order_by('-mes')

    # 6. Alertas de Vencimiento
    hoy = timezone.localdate()
    limite = hoy + timedelta(days=30)
    
    tarjetas_por_vencer = operador.tarjeta_operador.filter(
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
    response['Content-Disposition'] = f'inline; filename="Reporte_{operador.organizacion.nombre}.pdf"'

    # 10. Generar el PDF (Usar utf-8 es crucial)
    pisa_status = pisa.CreatePDF(html.encode('utf-8'), dest=response)

    if pisa_status.err:
        return HttpResponse('Hubo un error al generar el PDF: <pre>' + html + '</pre>')
    
    return response