from django.shortcuts import render, get_object_or_404, redirect
from .models import Operador
from .forms import OperadorForm

def lista_operadores (request):
    operadores = Operador.objects.all()
    contexto = {
        'operadores': operadores
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