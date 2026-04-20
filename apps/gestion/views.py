
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import HistorialAccion
from apps.usuario.forms import PerfilForm, UsuarioForm
from django.contrib.auth import login, logout
from django.db import transaction
from apps.usuario.permisos import es_admin, es_usuario_normal, es_superadmin
from apps.operador.models import Operador
from apps.operador.forms import OperadorForm
from django.contrib import messages

# # Función auxiliar para el decorador: verifica si es superusuario
# def es_superadmin(user):
#     return user.is_superuser

# # Aplicamos el decorador para que solo los superadmins pasen de aquí
# @user_passes_test(es_superadmin)
def historial_list_view(request):
    # 1. Obtener todos los registros de la base de datos
    # (Ya vienen ordenados del más reciente al más antiguo por la clase Meta del modelo)
    lista_logs = HistorialAccion.objects.all()

    # 2. Configurar el paginador (mostrar 20 registros por página)
    paginator = Paginator(lista_logs, 20)

    # 3. Capturar el número de página que el usuario pide en la URL (ej. /auditoria/?page=2)
    # Si no hay parámetro 'page', por defecto será la página 1
    page_number = request.GET.get('page', 1)

    try:
        # Intentar obtener los registros de esa página exacta
        logs = paginator.page(page_number)
    except PageNotAnInteger:
        # Si alguien escribe letras en la URL (ej. ?page=hola), lo mandamos a la página 1
        logs = paginator.page(1)
    except EmptyPage:
        # Si piden una página que no existe (ej. la 9999), les damos la última página válida
        logs = paginator.page(paginator.num_pages)

    # 4. Empaquetar los datos en un diccionario de contexto
    context = {
        'logs': logs,
    }

    # 5. Renderizar la plantilla enviando el contexto
    return render(request, 'gestion/historial_list.html', context)

def logup_view (request):
    if request.method == 'POST':
        usuario_form = UsuarioForm(request.POST, prefix='usaurio')
        perfil_form = PerfilForm(request.POST, prefix='perfil')
        if usuario_form.is_valid() and perfil_form.is_valid():
            try:
                with transaction.atomic():
                    usuario = usuario_form.save()
                    perfil = perfil_form.save(commit=False)
                    perfil.usuario = usuario
                    perfil.save()
                    login(request, usuario)
                return redirect('home')

            except Exception as e:
                print(e)
    else:
        usuario_form = UsuarioForm(prefix='usaurio')
        perfil_form = PerfilForm(prefix='perfil')
    contexto = {
        'usuario_form': usuario_form,
        'perfil_form': perfil_form,
    }
    return render(request, 'usuario/logup.html', contexto)

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def operador_list(request):
    operadores = Operador.objects.all().order_by('-fecha_registro')
    return render(request, 'gestion/operador_list.html', {'operadores': operadores})

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def crear_operador(request):
    if request.method == 'POST':
        form = OperadorForm(request.POST)
        if form.is_valid():
            operador = form.save()
            messages.success(request, f"Operador '{operador.nombre}' registrado con éxito.")
            return redirect('gestion:operador_list')
        else:
            messages.error(request, "Error al registrar. Verifique los datos.")
    else:
        form = OperadorForm()
        
    return render(request, 'gestion/operador_form.html', {'form': form, 'accion': 'Crear'})

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def editar_operador(request, pk):
    operador = get_object_or_404(Operador, pk=pk)
    if request.method == 'POST':
        form = OperadorForm(request.POST, instance=operador)
        if form.is_valid():
            form.save()
            messages.success(request, f"Operador '{operador.nombre}' actualizado correctamente.")
            return redirect('gestion:operador_list')
    else:
        form = OperadorForm(instance=operador)
        
    return render(request, 'gestion/operador_form.html', {'form': form, 'accion': 'Editar'})

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def eliminar_operador(request, pk):
    operador = get_object_or_404(Operador, pk=pk)
    if request.method == 'POST':
        nombre = operador.nombre
        operador.delete()
        messages.success(request, f"El operador '{nombre}' ha sido eliminado del sistema.")
        return redirect('gestion:operador_list')
    # No necesitamos un template separado porque usamos el Modal de la lista
    return redirect('gestion:operador_list')