import json
import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction, DatabaseError
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import HttpRequest, HttpResponse

from apps.operador.models import Operador
from apps.afiliado.models import Afiliado
from apps.vehiculo.models import Vehiculo
from apps.tramite.models import Tramite
from apps.tarjeta_de_operacion.models import TarjetaDeOperacion
from apps.usuario.models import Usuario, Perfil
from apps.usuario.forms import UsuarioCreationForm, UsuarioUpdateForm, PerfilForm
from .permisos import es_admin, es_usuario_normal, es_superadmin

logger = logging.getLogger(__name__)

@login_required
@user_passes_test(es_usuario_normal, login_url='/', redirect_field_name=None)
def home(request: HttpRequest) -> HttpResponse:
    try:
        total_operadores = Operador.objects.count()
        total_afiliados = Afiliado.objects.count()
        total_vehiculos = Vehiculo.objects.count()
        tramites_pendientes = Tramite.objects.filter(estado='p').count()
        ultimos_tramites = Tramite.objects.order_by('-fecha_registro')[:5]

        tarjetas_por_tipo = TarjetaDeOperacion.objects.values('ruta').annotate(total=Count('id'))
        tipos_dict = dict(getattr(TarjetaDeOperacion, 'RUTAS_CHOICES', ()))
        
        tipo_labels = [tipos_dict.get(item['ruta'], item['ruta'] or 'Sin asignar') for item in tarjetas_por_tipo]
        tipo_data = [item['total'] for item in tarjetas_por_tipo]

        seis_meses_atras = timezone.now() - timedelta(days=6*30)
        emisiones = TarjetaDeOperacion.objects.filter(fecha_registro__gte=seis_meses_atras) \
            .annotate(mes=TruncMonth('fecha_registro')) \
            .values('mes') \
            .annotate(total=Count('id')) \
            .order_by('mes')

        meses_nombres = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 
                         7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
        
        bar_labels = [f"{meses_nombres[e['mes'].month]} {e['mes'].year}" for e in emisiones if e.get('mes')]
        bar_data = [e['total'] for e in emisiones if e.get('mes')]
        
    except DatabaseError as e:
        logger.error(f"Error de base de datos al cargar el dashboard: {e}")
        messages.error(request, "Ocurrió un problema al cargar los datos del dashboard.")
        return render(request, 'home.html', {})

    contexto = {
        'total_operadores': total_operadores,
        'total_afiliados': total_afiliados,
        'total_vehiculos': total_vehiculos,
        'tramites_pendientes': tramites_pendientes,
        'ultimos_tramites': ultimos_tramites,
        'tipo_labels': json.dumps(tipo_labels),
        'tipo_data': json.dumps(tipo_data),
        'bar_labels': json.dumps(bar_labels),
        'bar_data': json.dumps(bar_data),
    }

    return render(request, 'home.html', contexto)

def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect('login')


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('home')
        
    form = AuthenticationForm(request, data=request.POST) if request.method == 'POST' else AuthenticationForm()
    
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('home')

    return render(request, 'usuario/login.html', {'form': form})

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def usuario_list(request: HttpRequest) -> HttpResponse:
    usuarios = Usuario.objects.select_related('perfil').all().order_by('-date_joined')
    return render(request, 'gestion/usuario_list.html', {'usuarios': usuarios})

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def usuario_detail(request: HttpRequest, pk: int) -> HttpResponse:
    usuario_obj = get_object_or_404(Usuario.objects.select_related('perfil'), pk=pk)
    return render(request, 'gestion/usuario_detail.html', {'usuario_obj': usuario_obj})

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
@transaction.atomic
def crear_usuario(request: HttpRequest) -> HttpResponse:
    usuario_form = UsuarioCreationForm(request.POST or None)
    perfil_form = PerfilForm(request.POST or None)
    
    if request.method == 'POST' and usuario_form.is_valid() and perfil_form.is_valid():
        try:
            nuevo_usuario = usuario_form.save()
            perfil = perfil_form.save(commit=False)
            perfil.usuario = nuevo_usuario
            perfil.save()
            
            messages.success(request, f"Usuario {nuevo_usuario.username} provisionado correctamente.")
            return redirect('gestion:usuario_list')
        except Exception as e:
            logger.error(f"Error al intentar crear el usuario: {e}")
            messages.error(request, "Error interno al intentar provisionar el usuario.")
    elif request.method == 'POST':
        messages.warning(request, "Por favor, corrija los errores en el formulario.")

    context = {
        'usuario_form': usuario_form,
        'perfil_form': perfil_form,
        'accion': 'Crear'
    }
    return render(request, 'gestion/usuario_form.html', context)

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
@transaction.atomic
def editar_usuario(request: HttpRequest, pk: int) -> HttpResponse:
    usuario = get_object_or_404(Usuario, pk=pk)
    perfil = get_object_or_404(Perfil, usuario=usuario)
    
    usuario_form = UsuarioUpdateForm(request.POST or None, instance=usuario)
    perfil_form = PerfilForm(request.POST or None, instance=perfil)
    
    if request.method == 'POST' and usuario_form.is_valid() and perfil_form.is_valid():
        try:
            usuario_form.save()
            perfil_form.save()
            messages.success(request, f"Credenciales y Perfil de {usuario.username} actualizados.")
            return redirect('gestion:usuario_list')
        except Exception as e:
            logger.error(f"Error al editar el usuario {pk}: {e}")
            messages.error(request, "Error interno al intentar actualizar el usuario.")
    elif request.method == 'POST':
        messages.warning(request, "Por favor, corrija los errores en el formulario.")
        
    context = {
        'usuario_form': usuario_form,
        'perfil_form': perfil_form,
        'accion': 'Editar'
    }
    return render(request, 'gestion/usuario_form.html', context)

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def eliminar_usuario(request: HttpRequest, pk: int) -> HttpResponse:
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        try:
            nombre_usuario = usuario.username
            usuario.delete()
            messages.success(request, f"El usuario {nombre_usuario} ha sido dado de baja permanentemente.")
            return redirect('gestion:usuario_list')
        except Exception as e:
            logger.error(f"Error al intentar eliminar el usuario {pk}: {e}")
            messages.error(request, "No se pudo eliminar el usuario debido a un error interno de base de datos.")
            
    return render(request, 'gestion/usuario_confirm_delete.html', {'usuario_obj': usuario})