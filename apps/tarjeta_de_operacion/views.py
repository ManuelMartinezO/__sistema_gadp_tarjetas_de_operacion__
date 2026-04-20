from django.shortcuts import render, redirect, get_object_or_404
from .models import TarjetaDeOperacion
from .forms import TarjetaDeOperacionForm

from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
import io
import qrcode
import base64
from django.db.models import Q
from django.http import JsonResponse
from .forms import RutaForm  # Asegúrate de importar tu formulario
from apps.tramite.models import Tramite
from django.core.paginator import Paginator

def lista_tarjetas(request):
    # Optimización: select_related para evitar consultas N+1
    tarjetas_list = TarjetaDeOperacion.objects.select_related(
        'vehiculo', 'afiliado', 'operador', 'ruta', 'tramite'
    ).all().order_by('-id')

    # 1. Capturar parámetros
    q = request.GET.get('q', '').strip()
    ruta_q = request.GET.get('ruta', '').strip()
    tipo = request.GET.get('tipo', 'todos')
    estado = request.GET.get('estado', 'todos')

    # 2. Búsqueda General
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

    # 3. Búsqueda por Ruta
    if ruta_q:
        tarjetas_list = tarjetas_list.filter(ruta__ruta__icontains=ruta_q)

    # 4. Filtro por Tipo
    if tipo and tipo != 'todos':
        tarjetas_list = tarjetas_list.filter(tipo_tarjeta=tipo)

    # 5. Filtro por Estado
    if estado != 'todos':
        if estado == 'emitida':
            tarjetas_list = tarjetas_list.filter(fecha_emision__isnull=False)
        elif estado == 'pendiente':
            tarjetas_list = tarjetas_list.filter(fecha_emision__isnull=True)

    # 6. Paginación
    paginator = Paginator(tarjetas_list, 5)
    page_number = request.GET.get('page')
    tarjetas = paginator.get_page(page_number)

    contexto = {
        'tarjetas': tarjetas, # Objeto paginado
        'q': q,
        'ruta_q': ruta_q,
        'tipo_actual': tipo,
        'estado_actual': estado,
        'tipos_tarjeta': TarjetaDeOperacion.TIPO_TARJETA, 
    }
    return render(request, 'tarjeta/lista.html', contexto)
    
def detalle_tarjeta (request, id_tarjeta):
    tarjeta = get_object_or_404(TarjetaDeOperacion, id=id_tarjeta)
    contexto = {
        'tarjeta': tarjeta,
    }
    return render(request, 'tarjeta/detalle.html', contexto)

def crear_tarjeta (request, numero_tramite):
    tramite = get_object_or_404(Tramite, numero_tramite=numero_tramite)
    if request.method == 'POST':
        form = TarjetaDeOperacionForm(request.POST)
        if form.is_valid():
            guardado = form.save(commit=False)
            guardado.operador = tramite.operador
            guardado.save()
            return redirect('tarjeta:lista_tarjetas')
    else:
        form = TarjetaDeOperacionForm()
    contexto = {
        'form': form,
    }
    return render(request, 'tarjeta/crear.html', contexto)

def editar_tarjeta (request, id_tarjeta):
    tarjeta = get_object_or_404(TarjetaDeOperacion, id=id_tarjeta)
    if request.method == 'POST':
        form = TarjetaDeOperacionForm(request.POST, instance=tarjeta)
        if form.is_valid():
            guardado = form.save()
            return redirect('tarjeta:detalle_tarjeta', tarjeta.id)
    else:
        form = TarjetaDeOperacionForm(instance=tarjeta)
    contexto = {
        'form': form,
    }
    return render(request, 'tarjeta/editar.html', contexto)


def generar_pdf_tarjeta (request, id_tarjeta):
    tarjeta = get_object_or_404(TarjetaDeOperacion, id=id_tarjeta)
    texto_qr = (
        f"PLACA: {tarjeta.vehiculo.placa}\n"
        f"MARCA: {tarjeta.vehiculo.marca}\n"
        f"MODELO: {tarjeta.vehiculo.modelo}\n"
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
    qr_data_uri = f"data:image/png;base64,{imagen_base64}"
    contexto = {
        'tarjeta': tarjeta,
        'qr_data_uri': qr_data_uri,
    }
    template = get_template('pdf/tarjeta.html')
    template_render = template.render(contexto)
    response = HttpResponse(content_type = 'application/pdf')
    response['Content-Disposition'] = f'inline; filename="Tarjeta_Vehiculo_{tarjeta.vehiculo.placa}.pdf"'
    pisa_status = pisa.CreatePDF(template_render, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF')
    return response
    

def crear_ruta_ajax(request):
    # Verificamos que sea POST y que sea una petición AJAX
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = RutaForm(request.POST)
        if form.is_valid():
            nueva_ruta = form.save()
            return JsonResponse({
                'success': True, 
                'id': nueva_ruta.id, 
                'nombre': nueva_ruta.ruta
            })
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'error': 'Solicitud no válida'})