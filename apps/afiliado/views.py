import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse
from apps.usuario.permisos import es_admin, es_usuario_normal, es_superadmin
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Afiliado
from .forms import EditarAfiliadoForm

logger = logging.getLogger(__name__)

@login_required
@user_passes_test(es_admin, login_url='/', redirect_field_name=None)
def lista_afiliados(request: HttpRequest) -> HttpResponse:
    q = request.GET.get('q', '').strip()
    
    try:
        afiliados_list = Afiliado.objects.select_related(
            'operador__organizacion', 
            'operador__federacion'
        ).all().order_by('-fecha_registro')
        
        if q:
            afiliados_list = afiliados_list.filter(
                Q(nombre_completo__icontains=q) |
                Q(operador__organizacion__nombre__icontains=q) |
                Q(operador__federacion__nombre__icontains=q)
            )
            
        paginator = Paginator(afiliados_list, 5)
        page_number = request.GET.get('page')
        afiliados = paginator.get_page(page_number)
        
    except DatabaseError as e:
        logger.error(f"Error de DB en lista_afiliados: {e}")
        messages.error(request, "Ocurrió un error al cargar la lista de afiliados.")
        afiliados = []
        
    contexto = {
        'afiliados': afiliados,
        'q': q,
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'afiliado/parcial_tabla.html', contexto)

    return render(request, 'afiliado/lista.html', contexto)

@login_required
@user_passes_test(es_admin, login_url='/', redirect_field_name=None)
def detalle_afiliado(request: HttpRequest, id_afiliado: int) -> HttpResponse:
    afiliado = get_object_or_404(Afiliado.objects.select_related('operador'), id=id_afiliado)
    form_afiliado = EditarAfiliadoForm(instance=afiliado)
    
    if request.method == 'POST':
        if 'submit_afiliado' in request.POST:
            form_afiliado = EditarAfiliadoForm(request.POST, instance=afiliado)
            if form_afiliado.is_valid():
                try:
                    form_afiliado.save()
                    messages.success(request, "Datos actualizados correctamente.")
                    return redirect('afiliado:detalle_afiliado', id_afiliado=afiliado.id)
                except Exception as e:
                    logger.error(f"Error al guardar afiliado {id_afiliado}: {e}")
                    messages.error(request, "Error inesperado al guardar los cambios.")

    contexto = {
        'afiliado': afiliado,
        'form_afiliado': form_afiliado,
    }
    
    return render(request, 'afiliado/detalle.html', contexto)