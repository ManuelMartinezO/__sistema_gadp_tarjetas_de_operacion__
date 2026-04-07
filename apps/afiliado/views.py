from django.shortcuts import render, get_object_or_404, redirect
from .models import Afiliado
from .forms import AfiliadoForm

def lista_afiliados (request):
    afiliados = Afiliado.objects.all()
    contexto = {
        'afiliados': afiliados
    }
    return render(request, 'afiliado/lista.html', contexto)
    
def detalle_afiliado (request, id_afiliado):
    afiliado = get_object_or_404(Afiliado, id=id_afiliado)
    contexto = {
        'afiliado': afiliado,
    }
    return render(request, 'afiliado/detalle.html', contexto)

def crear_afiliado (request):
    if request.method == 'POST':
        form = AfiliadoForm(request.POST)
        if form.is_valid():
            guardado = form.save()
            return redirect('afiliado:lista_afiliados')
    else:
        form = AfiliadoForm()
    contexto = {
        'form': form
    }
    return render(request, 'afiliado/crear.html', contexto)