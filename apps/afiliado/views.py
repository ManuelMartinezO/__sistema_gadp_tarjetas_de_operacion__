from django.shortcuts import render, get_object_or_404, redirect
from .models import Afiliado
from .forms import AfiliadoForm
from django.db.models import Q

def lista_afiliados(request):
    # Usamos select_related('operador') para optimizar las consultas a la base de datos
    # ya que en el HTML mostramos el nombre de la empresa de cada afiliado.
    afiliados = Afiliado.objects.select_related('operador').all().order_by('-fecha_registro')
    
    # 1. Capturamos el texto del buscador
    q = request.GET.get('q', '').strip()
    
    # 2. Filtramos por nombre, apellido o nombre de la empresa operadora
    if q:
        afiliados = afiliados.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(operador__nombre__icontains=q)
        )
        
    contexto = {
        'afiliados': afiliados,
        'q': q, # Para que el texto se mantenga en el input
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

def editar_afiliado (request, id_afiliado):
    afiliado = get_object_or_404(Afiliado, id=id_afiliado)
    if request.method == 'POST':
        form = AfiliadoForm(request.POST, instance=afiliado)
        if form.is_valid():
            guardado = form.save()
            return redirect('afiliado:detalle_afiliado', afiliado.id)
    else:
        form = AfiliadoForm(instance=afiliado   )
    contexto = {
        'form': form
    }
    return render(request, 'afiliado/editar.html', contexto)