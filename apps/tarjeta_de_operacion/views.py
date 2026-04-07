from django.shortcuts import render, redirect, get_object_or_404
from .models import TarjetaDeOperacion
from .forms import TarjetaDeOperacionForm

def lista_tarjetas (request):
    tarjetas = TarjetaDeOperacion.objects.all()
    contexto = {
        'tarjetas': tarjetas
    }
    return render(request, 'tarjeta/lista.html', contexto)
    
def detalle_tarjeta (request, id_tarjeta):
    tarjeta = get_object_or_404(TarjetaDeOperacion, id=id_tarjeta)
    contexto = {
        'tarjeta': tarjeta,
    }
    return render(request, 'tarjeta/detalle.html', contexto)

def crear_tarjeta (request):
    if request.method == 'POST':
        form = TarjetaDeOperacionForm(request.POST)
        if form.is_valid():
            guardado = form.save()
            return redirect('tarjeta:lista_tarjetas')
    else:
        form = TarjetaDeOperacionForm()
    contexto = {
        'form': form,
    }
    return render(request, 'tarjeta/crear.html', contexto)
