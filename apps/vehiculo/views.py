import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpRequest, HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import DatabaseError

from .models import Vehiculo
from .forms import TipoVehiculoForm, MarcaVehiculoForm, EditarVehiculoForm

logger = logging.getLogger(__name__)

def lista_vehiculos(request: HttpRequest) -> HttpResponse:
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'todos')
    
    try:
        vehiculos_list = Vehiculo.objects.select_related(
            'marca', 'tipo', 'afiliado'
        ).all().order_by('-fecha_registro')
        
        if q:
            filtros = Q(placa__icontains=q) | Q(marca__nombre__icontains=q)
            if q.isdigit():
                filtros |= Q(modelo=q)
            vehiculos_list = vehiculos_list.filter(filtros)
            
        if tipo and tipo != 'todos':
            vehiculos_list = vehiculos_list.filter(transporte=tipo)

        paginator = Paginator(vehiculos_list, 5)
        page_number = request.GET.get('page')
        vehiculos = paginator.get_page(page_number)
        
    except DatabaseError as e:
        logger.error(f"Error de base de datos en lista_vehiculos: {e}")
        messages.error(request, "Ocurrió un error al cargar la lista de vehículos.")
        vehiculos = []
        
    contexto = {
        'vehiculos': vehiculos,
        'q': q,
        'tipo_actual': tipo,
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'vehiculo/parcial_tabla.html', contexto)
        
    return render(request, 'vehiculo/lista.html', contexto)

def detalle_vehiculo(request: HttpRequest, placa: str) -> HttpResponse:
    vehiculo = get_object_or_404(
        Vehiculo.objects.select_related('marca', 'tipo', 'afiliado'), 
        placa=placa
    )
    
    form_vehiculo = EditarVehiculoForm(instance=vehiculo)
    form_marca = MarcaVehiculoForm()
    form_tipo = TipoVehiculoForm()
    
    if request.method == 'POST':
        try:
            if 'submit_vehiculo' in request.POST:
                form_vehiculo = EditarVehiculoForm(request.POST, instance=vehiculo)
                if form_vehiculo.is_valid():
                    vehiculo_guardado = form_vehiculo.save()
                    messages.success(request, "Datos del vehículo actualizados correctamente.")
                    return redirect('vehiculo:detalle_vehiculo', placa=vehiculo_guardado.placa)
                    
            elif 'submit_marca' in request.POST:
                form_marca = MarcaVehiculoForm(request.POST)
                if form_marca.is_valid():
                    form_marca.save()
                    messages.success(request, "Nueva marca registrada y disponible.")
                    return redirect('vehiculo:detalle_vehiculo', placa=vehiculo.placa)
                    
            elif 'submit_tipo' in request.POST:
                form_tipo = TipoVehiculoForm(request.POST)
                if form_tipo.is_valid():
                    form_tipo.save()
                    messages.success(request, "Nuevo tipo de vehículo registrado.")
                    return redirect('vehiculo:detalle_vehiculo', placa=vehiculo.placa)
                    
        except Exception as e:
            logger.error(f"Error al actualizar vehículo {placa}: {e}")
            messages.error(request, "Error inesperado al procesar los datos.")

    contexto = {
        'vehiculo': vehiculo,
        'form_vehiculo': form_vehiculo,
        'form_marca': form_marca,
        'form_tipo': form_tipo,
    }
    return render(request, 'vehiculo/detalle.html', contexto)