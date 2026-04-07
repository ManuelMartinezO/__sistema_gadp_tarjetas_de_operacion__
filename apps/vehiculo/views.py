from django.shortcuts import render, get_object_or_404, redirect
from .models import ColorVehiculo, TipoVehiculo, MarcaVehiculo, Vehiculo
from .forms import ColorVehiculoForm, TipoVehiculoForm, MarcaVehiculoForm, VehiculoForm
from django.http import JsonResponse

def lista_vehiculos (request):
    vehiculos = Vehiculo.objects.all()
    contexto = {
        'vehiculos': vehiculos
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


# === AJAX ===

# def crear_color(request):
#     if request.method == 'POST':
#         # Obtenemos el dato que envía el modal
#         nombre_color = request.POST.get('nombre')
        
#         if nombre_color:
#             # Creamos el registro en la base de datos
#             nuevo_color = ColorVehiculo.objects.create(nombre=nombre_color)
            
#             # Devolvemos el ID y el Nombre para que JS actualice el formulario
#             return JsonResponse({'id': nuevo_color.id, 'nombre': nuevo_color.nombre})
            
#     return JsonResponse({'error': 'Error al crear'}, status=400)

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