from django.shortcuts import render, get_object_or_404, redirect
from .models import Afiliado
from django.db.models import Q
from django.core.paginator import Paginator
from .forms import EditarAfiliadoForm

def lista_afiliados(request):
    # 1. ACTUALIZACIÓN: Optimizamos trayendo hasta la organización y federación
    afiliados_list = Afiliado.objects.select_related(
        'operador__organizacion', 
        'operador__federacion'
    ).all().order_by('-fecha_registro')
    
    # 2. Búsqueda actualizada a la nueva estructura del Operador
    q = request.GET.get('q', '').strip()
    if q:
        afiliados_list = afiliados_list.filter(
            Q(nombre_completo__icontains=q) |
            Q(operador__organizacion__nombre__icontains=q) | # Busca por organización
            Q(operador__federacion__nombre__icontains=q)    # Busca por federación
        )
        
    # 3. Paginación
    paginator = Paginator(afiliados_list, 5)
    page_number = request.GET.get('page')
    afiliados = paginator.get_page(page_number)
        
    contexto = {
        'afiliados': afiliados,
        'q': q,
    }
    
    # Detectar si es una petición AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'afiliado/parcial_tabla.html', contexto)

    return render(request, 'afiliado/lista.html', contexto)
    
def detalle_afiliado(request, id_afiliado):
    # Optimizamos para traer los datos del operador en la misma consulta
    afiliado = get_object_or_404(Afiliado.objects.select_related('operador'), id=id_afiliado)
    
    # Instanciamos el formulario con los datos actuales
    form_afiliado = EditarAfiliadoForm(instance=afiliado)
    
    # Procesamos la petición si se envió el formulario
    if request.method == 'POST':
        if 'submit_afiliado' in request.POST:
            form_afiliado = EditarAfiliadoForm(request.POST, instance=afiliado)
            if form_afiliado.is_valid():
                form_afiliado.save()
                return redirect('afiliado:detalle_afiliado', id_afiliado=afiliado.id)

    contexto = {
        'afiliado': afiliado,
        'form_afiliado': form_afiliado,
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