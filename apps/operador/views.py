from django.shortcuts import render, get_object_or_404, redirect
from .models import Operador
from .forms import OperadorForm

def lista_operadores(request):
    # Obtenemos todos los operadores, ordenados por fecha (opcional pero recomendado)
    operadores = Operador.objects.all().order_by('-fecha_registro')
    
    # 1. Capturar lo que el usuario escribe en el buscador
    q = request.GET.get('q', '').strip()
    
    # 2. Si hay texto, filtramos por el nombre
    if q:
        operadores = operadores.filter(nombre__icontains=q)
        
    contexto = {
        'operadores': operadores,
        'q': q, # Pasamos la búsqueda al contexto para que no se borre del input
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