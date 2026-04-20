from django.shortcuts import render, get_object_or_404, redirect
from .models import Afiliado
from .forms import AfiliadoForm
from django.db.models import Q
from django.core.paginator import Paginator

def lista_afiliados(request):
    # Consulta optimizada con select_related
    afiliados_list = Afiliado.objects.select_related('operador').all().order_by('-fecha_registro')
    
    # 1. Búsqueda
    q = request.GET.get('q', '').strip()
    if q:
        afiliados_list = afiliados_list.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(operador__nombre__icontains=q)
        )
        
    # 2. Paginación (Mostramos 10 por página)
    paginator = Paginator(afiliados_list, 5)
    page_number = request.GET.get('page')
    afiliados = paginator.get_page(page_number)
        
    contexto = {
        'afiliados': afiliados,
        'q': q,
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