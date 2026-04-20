from django.shortcuts import render, get_object_or_404, redirect
from .models import ColorVehiculo, TipoVehiculo, MarcaVehiculo, Vehiculo
from .forms import ColorVehiculoForm, TipoVehiculoForm, MarcaVehiculoForm, VehiculoForm
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator

def lista_vehiculos(request):
    # Optimizamos consultas
    vehiculos_list = Vehiculo.objects.select_related(
        'marca', 'tipo_vehiculo', 'propietario'
    ).all().order_by('-fecha_registro')
    
    # 1. Capturar parámetros
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', 'todos')
    
    # 2. Filtrado por texto
    if q:
        filtros = Q(placa__icontains=q) | Q(marca__nombre__icontains=q)
        if q.isdigit():
            filtros |= Q(modelo=q)
        vehiculos_list = vehiculos_list.filter(filtros)
        
    # 3. Filtrado por Tipo
    if tipo and tipo != 'todos':
        vehiculos_list = vehiculos_list.filter(tipo_transporte=tipo)

    # 4. Paginación
    paginator = Paginator(vehiculos_list, 5)
    page_number = request.GET.get('page')
    vehiculos = paginator.get_page(page_number)
        
    contexto = {
        'vehiculos': vehiculos, # Objeto paginado
        'q': q,
        'tipo_actual': tipo,
    }
    return render(request, 'vehiculo/lista.html', contexto)

def detalle_vehiculo (request, placa):
    vehiculo = get_object_or_404(Vehiculo, placa=placa)
    contexto = {
        'vehiculo': vehiculo,
    }
    return render(request, 'vehiculo/detalle.html', contexto)

def crear_vehiculo (request):
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            guardado = form.save()
            return redirect('vehiculo:lista_vehiculos')
    else:
        form = VehiculoForm()
    contexto = {
        'form': form,
        'form_color': ColorVehiculoForm(),
        'form_marca': MarcaVehiculoForm(),
        'form_tipo': TipoVehiculoForm(),
    }
    return render(request, 'vehiculo/crear.html', contexto)

def editar_vehiculo (request, placa):
    vehiculo = get_object_or_404(Vehiculo, placa=placa)
    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            guardado = form.save()
            return redirect('vehiculo:detalle_vehiculo', vehiculo.placa)
    else:
        form = VehiculoForm(instance=vehiculo)
    contexto = {
        'form': form,
    }
    return render(request, 'vehiculo/editar.html', contexto)

# === AJAX ===

def crear_atributo (request):
    if request.method == 'POST':
        # Capturamos el identificador oculto ('color', 'marca' o 'tipo')
        tipo_atributo = request.POST.get('tipo_atributo')
        
        # Diccionario que conecta el string con la Clase del Formulario
        formularios = {
            'color': ColorVehiculoForm,
            'marca': MarcaVehiculoForm,
            'tipo_vehiculo': TipoVehiculoForm,
        }
        
        # Obtenemos la clase correcta según lo que envió el HTML
        FormClass = formularios.get(tipo_atributo)
        
        # Si alguien envía un dato modificado maliciosamente que no está en el diccionario
        if not FormClass:
            return JsonResponse({'error': 'Tipo no válido'}, status=400)
            
        # Instanciamos el formulario dinámicamente con los datos
        form = FormClass(request.POST)
        
        if form.is_valid():
            nuevo_objeto = form.save()
            return JsonResponse({
                'id': nuevo_objeto.id, 
                'nombre': str(nuevo_objeto),
                'tipo': tipo_atributo # Devolvemos el tipo para saber qué select actualizar en JS
            })
        else:
            return JsonResponse({'errores': form.errors}, status=400)
            
    return JsonResponse({'error': 'Método no permitido'}, status=405)