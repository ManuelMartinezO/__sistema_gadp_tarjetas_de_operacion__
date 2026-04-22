from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from .forms import UsuarioForm, PerfilForm
from apps.operador.models import Operador
from apps.afiliado.models import Afiliado
from apps.vehiculo.models import Vehiculo
from apps.tramite.models import Tramite
from apps.tarjeta_de_operacion.models import TarjetaDeOperacion
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncMonth
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from .permisos import es_admin, es_usuario_normal, es_superadmin
from django.contrib.auth import login, logout
from django.db import transaction
from apps.usuario.models import Usuario, Perfil
from django.contrib import messages
from apps.usuario.forms import UsuarioCreationForm, UsuarioUpdateForm, PerfilForm

# === HOME ===
@login_required()
@user_passes_test(es_usuario_normal)
def home (request):
    total_operadores = Operador.objects.count() 
    total_afiliados = Afiliado.objects.count()
    total_vehiculos = Vehiculo.objects.count()
    tramites_pendientes = Tramite.objects.filter(estado_tramite='pendiente').count()
    ultimos_tramites = Tramite.objects.order_by('-fecha_registro')[:5]

    tarjetas_por_tipo = TarjetaDeOperacion.objects.values('tipo_tarjeta').annotate(total=Count('id'))
    
    # Diccionario para traducir '001' a 'InterProvincial', etc.
    tipos_dict = dict(TarjetaDeOperacion.TIPO_TARJETA) 
    
    tipo_labels = []
    tipo_data = []
    for item in tarjetas_por_tipo:
        tipo_labels.append(tipos_dict.get(item['tipo_tarjeta'], 'Otros'))
        tipo_data.append(item['total'])

    # 3. Datos para el Gráfico de Barras (Últimos 6 meses)
    seis_meses_atras = timezone.now() - timedelta(days=6*30)
    
    emisiones = TarjetaDeOperacion.objects.filter(fecha_registro__gte=seis_meses_atras) \
        .annotate(mes=TruncMonth('fecha_registro')) \
        .values('mes') \
        .annotate(total=Count('id')) \
        .order_by('mes')

    meses_nombres = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
    
    bar_labels = []
    bar_data = []
    for e in emisiones:
        if e['mes']:
            nombre_mes = f"{meses_nombres[e['mes'].month]} {e['mes'].year}"
            bar_labels.append(nombre_mes)
            bar_data.append(e['total'])

    # 4. Enviar todo al template
    contexto = {
        'total_operadores': total_operadores,
        'total_afiliados': total_afiliados,
        'total_vehiculos': total_vehiculos,
        'tramites_pendientes': tramites_pendientes,
        'ultimos_tramites': ultimos_tramites,
        # Pasamos las listas convertidas a JSON para que JavaScript las entienda
        'tipo_labels': json.dumps(tipo_labels),
        'tipo_data': json.dumps(tipo_data),
        'bar_labels': json.dumps(bar_labels),
        'bar_data': json.dumps(bar_data),
    }

    return render(request, 'home.html', contexto)

# === LOGUP ===


# === LOGOUT ===
def logout_view (request):
    logout(request)
    return redirect('login')

# === LOGIN ===
def login_view (request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            return redirect('home')
    else:
        form = AuthenticationForm()
    contexto = {
        'form': form,
    }
    return render(request, 'usuario/login.html', contexto)


@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def usuario_list(request):
    """Lista todos los usuarios registrados."""
    # select_related optimiza la consulta cruzada con Perfil
    usuarios = Usuario.objects.select_related('perfil').all().order_by('-date_joined')
    
    context = {
        'usuarios': usuarios
    }
    return render(request, 'gestion/usuario_list.html', context)


@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def usuario_detail(request, pk):
    """Muestra los detalles de un usuario específico."""
    usuario_obj = get_object_or_404(Usuario.objects.select_related('perfil'), pk=pk)
    
    context = {
        'usuario_obj': usuario_obj
    }
    return render(request, 'gestion/usuario_detail.html', context)


# @login_required
# @user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
@transaction.atomic  # CRÍTICO: Asegura que ambos formularios se guarden o ninguno
def crear_usuario(request):
    """Crea un Usuario y su Perfil al mismo tiempo."""
    if request.method == 'POST':
        usuario_form = UsuarioCreationForm(request.POST)
        perfil_form = PerfilForm(request.POST)
        
        if usuario_form.is_valid() and perfil_form.is_valid():
            # 1. Guardamos el Usuario (Hashea la contraseña)
            nuevo_usuario = usuario_form.save()
            
            # 2. Guardamos el Perfil vinculándolo al usuario creado
            perfil = perfil_form.save(commit=False)
            perfil.usuario = nuevo_usuario
            perfil.save()
            
            messages.success(request, f"Usuario {nuevo_usuario.username} provisionado correctamente.")
            return redirect('gestion:usuario_list')
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else:
        usuario_form = UsuarioCreationForm()
        perfil_form = PerfilForm()
        
    context = {
        'usuario_form': usuario_form,
        'perfil_form': perfil_form,
        'accion': 'Crear'
    }
    return render(request, 'gestion/usuario_form.html', context)


@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
@transaction.atomic
def editar_usuario(request, pk):
    """Edita las credenciales de un Usuario y sus datos de Perfil."""
    usuario = get_object_or_404(Usuario, pk=pk)
    perfil = get_object_or_404(Perfil, usuario=usuario)
    
    if request.method == 'POST':
        usuario_form = UsuarioUpdateForm(request.POST, instance=usuario)
        perfil_form = PerfilForm(request.POST, instance=perfil)
        
        if usuario_form.is_valid() and perfil_form.is_valid():
            usuario_form.save()
            perfil_form.save()
            
            messages.success(request, f"Credenciales y Perfil de {usuario.username} actualizados.")
            return redirect('gestion:usuario_list')
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
    else:
        usuario_form = UsuarioUpdateForm(instance=usuario)
        perfil_form = PerfilForm(instance=perfil)
        
    context = {
        'usuario_form': usuario_form,
        'perfil_form': perfil_form,
        'accion': 'Editar'
    }
    return render(request, 'gestion/usuario_form.html', context)


@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def eliminar_usuario(request, pk):
    """Da de baja a un usuario del sistema."""
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        nombre_usuario = usuario.username
        usuario.delete() # El Perfil se elimina automáticamente por el on_delete=CASCADE
        
        messages.success(request, f"El usuario {nombre_usuario} ha sido dado de baja permanentemente.")
        return redirect('gestion:usuario_list')
        
    context = {
        'usuario_obj': usuario
    }
    return render(request, 'gestion/usuario_confirm_delete.html', context)