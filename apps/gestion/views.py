# 1. Librerías estándar de Python
from collections import defaultdict

# 2. Librerías de terceros
from auditlog.models import LogEntry
from xhtml2pdf import pisa

# 3. Módulos de Django
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction, DatabaseError
from django.db.models import Q, Count
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.db.models.functions import TruncMonth

# Apps: Afiliado
from apps.afiliado.models import Afiliado
from apps.afiliado.forms import EditarAfiliadoForm

# Apps: Operador
from apps.operador.models import Operador, Federacion, Organizacion
from apps.operador.forms import NuevoOperadorForm, OrganizacionForm, FederacionForm

# Apps: Tarjeta de Operación
from apps.tarjeta_de_operacion.models import TarjetaDeOperacion
from apps.tarjeta_de_operacion.forms import EditarTarjetaForm

# Apps: Trámite
from apps.tramite.models import Tramite, Deposito
from apps.tramite.forms import EditarTramiteAdminForm, DepositoForm

# Apps: Usuario
from apps.usuario.forms import PerfilForm, UsuarioForm
from apps.usuario.permisos import es_admin, es_usuario_normal, es_superadmin

# Apps: Vehículo
from apps.vehiculo.models import Vehiculo, MarcaVehiculo, TipoVehiculo
from apps.vehiculo.forms import EditarVehiculoForm, MarcaVehiculoForm, TipoVehiculoForm

import logging

logger = logging.getLogger(__name__)

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def historial_list_view(request: HttpRequest) -> HttpResponse:
    date_start = request.GET.get('date_start', '').strip()
    date_end = request.GET.get('date_end', '').strip()
    user_filter = request.GET.get('user', '').strip()
    ip_filter = request.GET.get('ip', '').strip()
    action_filter = request.GET.get('action', '').strip()
    module_filter = request.GET.get('module', '').strip()
    
    try:
        lista_logs = LogEntry.objects.select_related('actor', 'content_type').all()
        
        if date_start:
            lista_logs = lista_logs.filter(timestamp__date__gte=date_start)
        if date_end:
            lista_logs = lista_logs.filter(timestamp__date__lte=date_end)
        if user_filter:
            lista_logs = lista_logs.filter(actor__username__icontains=user_filter)
        if ip_filter:
            lista_logs = lista_logs.filter(remote_addr__icontains=ip_filter)
        if action_filter and action_filter in ['0', '1', '2']:
            lista_logs = lista_logs.filter(action=int(action_filter))
        if module_filter:
            lista_logs = lista_logs.filter(content_type__model__icontains=module_filter)

        paginator = Paginator(lista_logs, 20)
        page_number = request.GET.get('page', 1)

        try:
            logs = paginator.page(page_number)
        except PageNotAnInteger:
            logs = paginator.page(1)
        except EmptyPage:
            logs = paginator.page(paginator.num_pages)
            
    except DatabaseError as e:
        logger.error(f"Error consultando historial: {e}")
        messages.error(request, "Error de base de datos al cargar el historial de acciones.")
        logs = []

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_string = query_params.urlencode()

    context = {
        'logs': logs,
        'date_start': date_start,
        'date_end': date_end,
        'user_filter': user_filter,
        'ip_filter': ip_filter,
        'action_filter': action_filter,
        'module_filter': module_filter,
        'query_string': query_string,
    }

    return render(request, 'gestion/historial_list.html', context)

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def logup_view(request: HttpRequest) -> HttpResponse:
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
                    
                messages.success(request, "Cuenta registrada e iniciada exitosamente.")
                return redirect('home')

            except Exception as e:
                logger.error(f"Error al registrar usuario: {e}")
                messages.error(request, "Ocurrió un error interno al crear la cuenta.")
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
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
def operador_list(request: HttpRequest) -> HttpResponse:
    try:
        operadores = Operador.objects.all().order_by('-fecha_registro')
    except DatabaseError as e:
        logger.error(f"Error consultando operadores: {e}")
        operadores = []
        messages.error(request, "Error al cargar la lista de operadores.")
        
    return render(request, 'gestion/operador_list.html', {'operadores': operadores})

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def crear_operador(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = PerfilForm(request.POST)
        if form.is_valid():
            try:
                operador = form.save()
                messages.success(request, f"Operador '{operador.nombre}' registrado con éxito.")
                return redirect('gestion:operador_list')
            except Exception as e:
                logger.error(f"Error al crear operador: {e}")
                messages.error(request, "Error interno al guardar el operador.")
        else:
            messages.error(request, "Error al registrar. Verifique los datos.")
    else:
        form = PerfilForm()
        
    return render(request, 'gestion/operador_form.html', {'form': form, 'accion': 'Crear'})

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def editar_operador(request: HttpRequest, pk: int) -> HttpResponse:
    operador = get_object_or_404(Operador, pk=pk)
    
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=operador)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"Operador '{operador.nombre}' actualizado correctamente.")
                return redirect('gestion:operador_list')
            except Exception as e:
                logger.error(f"Error al editar operador {pk}: {e}")
                messages.error(request, "Error interno al actualizar el operador.")
        else:
            messages.error(request, "Error al actualizar. Verifique los datos ingresados.")
    else:
        form = PerfilForm(instance=operador)
        
    return render(request, 'gestion/operador_form.html', {'form': form, 'accion': 'Editar'})

@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def eliminar_operador(request: HttpRequest, pk: int) -> HttpResponse:
    operador = get_object_or_404(Operador, pk=pk)
    
    if request.method == 'POST':
        nombre = operador.nombre
        try:
            operador.delete()
            messages.success(request, f"El operador '{nombre}' ha sido eliminado del sistema.")
        except Exception as e:
            logger.warning(f"Intento de eliminar operador en uso {pk}: {e}")
            messages.error(request, "No se puede eliminar el operador porque tiene registros asociados.")
            
    return redirect('gestion:operador_list')

# ==========================================
# VISTA: AFILIADOS
# ==========================================
@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def gestion_admin_afiliados(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        afiliado_id = request.POST.get('afiliado_id')
        afiliado = get_object_or_404(Afiliado, id=afiliado_id)

        if 'submit_editar' in request.POST:
            form_edicion = EditarAfiliadoForm(request.POST, instance=afiliado)
            if form_edicion.is_valid():
                try:
                    form_edicion.save()
                    messages.success(request, f"El afiliado {afiliado.nombre_completo} ha sido actualizado correctamente.")
                except Exception as e:
                    logger.error(f"Error guardando edición de afiliado {afiliado_id}: {e}")
                    messages.error(request, "Error interno al intentar guardar los cambios.")
            else:
                messages.error(request, "Error al actualizar el afiliado. Revisa los datos.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            try:
                nombre = afiliado.nombre_completo
                afiliado.delete()
                messages.success(request, f"El afiliado {nombre} fue eliminado definitivamente.")
            except Exception as e:
                logger.warning(f"Error eliminando afiliado {afiliado_id}: {e}")
                messages.error(request, "No se puede eliminar el afiliado porque tiene registros asociados.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
    
    try:
        afiliados_list = Afiliado.objects.select_related('operador').all().order_by('-fecha_registro')
        if q:
            afiliados_list = afiliados_list.filter(nombre_completo__icontains=q)

        paginator = Paginator(afiliados_list, 20)
        page_number = request.GET.get('page')
        afiliados = paginator.get_page(page_number)
    except DatabaseError as e:
        logger.error(f"Error de DB al listar afiliados: {e}")
        messages.error(request, "Error al cargar la lista de afiliados.")
        afiliados = []

    contexto = {
        'afiliados': afiliados,
        'q': q,
        'form_generico': EditarAfiliadoForm(),
    }
    return render(request, 'gestion/gestion_afiliados.html', contexto)


# ==========================================
# VISTA: ORGANIZACIONES
# ==========================================
@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def gestion_organizaciones(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        org_id = request.POST.get('registro_id')
        organizacion = get_object_or_404(Organizacion, id=org_id)

        if 'submit_editar' in request.POST:
            form = OrganizacionForm(request.POST, instance=organizacion)
            if form.is_valid():
                try:
                    form.save()
                    messages.success(request, "Organización actualizada correctamente.")
                except Exception as e:
                    logger.error(f"Error editando organización {org_id}: {e}")
                    messages.error(request, "Error al guardar los cambios.")
            else:
                messages.error(request, "Revisa los datos del formulario.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            try:
                organizacion.delete()
                messages.success(request, "Organización eliminada.")
            except Exception as e:
                logger.warning(f"Intento fallido de eliminar organización ligada {org_id}: {e}")
                messages.error(request, "No se puede eliminar porque está en uso por un Operador.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
    
    try:
        lista = Organizacion.objects.all().order_by('-fecha_registro')
        if q:
            lista = lista.filter(nombre__icontains=q)

        paginator = Paginator(lista, 20)
        registros = paginator.get_page(request.GET.get('page'))
    except DatabaseError as e:
        logger.error(f"Error listando organizaciones: {e}")
        registros = []

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': OrganizacionForm(),
        'titulo': 'Organizaciones',
        'icono': 'fa-sitemap'
    }
    return render(request, 'gestion/gestion_organizaciones.html', contexto)


# ==========================================
# VISTA: FEDERACIONES
# ==========================================
@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def gestion_federaciones(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        fed_id = request.POST.get('registro_id')
        federacion = get_object_or_404(Federacion, id=fed_id)

        if 'submit_editar' in request.POST:
            form = FederacionForm(request.POST, instance=federacion)
            if form.is_valid():
                try:
                    form.save()
                    messages.success(request, "Federación actualizada correctamente.")
                except Exception as e:
                    logger.error(f"Error editando federación {fed_id}: {e}")
                    messages.error(request, "Error al guardar cambios.")
            else:
                messages.error(request, "Datos inválidos en el formulario.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            try:
                federacion.delete()
                messages.success(request, "Federación eliminada.")
            except Exception as e:
                logger.warning(f"Intento fallido de eliminar federación en uso {fed_id}: {e}")
                messages.error(request, "No se puede eliminar porque está en uso.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
    
    try:
        lista = Federacion.objects.all().order_by('-fecha_registro')
        if q:
            lista = lista.filter(nombre__icontains=q)

        paginator = Paginator(lista, 20)
        registros = paginator.get_page(request.GET.get('page'))
    except DatabaseError as e:
        logger.error(f"Error listando federaciones: {e}")
        registros = []

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': FederacionForm(),
        'titulo': 'Federaciones',
        'icono': 'fa-layer-group'
    }
    return render(request, 'gestion/gestion_organizaciones.html', contexto)


# ==========================================
# VISTA: OPERADORES
# ==========================================
@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def gestion_operadores(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        op_id = request.POST.get('registro_id')
        operador = get_object_or_404(Operador, id=op_id)

        if 'submit_editar' in request.POST:
            form = NuevoOperadorForm(request.POST, instance=operador)
            if form.is_valid():
                try:
                    form.save()
                    messages.success(request, "Operador actualizado.")
                except Exception as e:
                    logger.error(f"Error editando operador {op_id}: {e}")
                    messages.error(request, "Error interno al actualizar el operador.")
            else:
                messages.error(request, "Error de validación en el formulario.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            try:
                operador.delete()
                messages.success(request, "Operador eliminado.")
            except Exception as e:
                logger.warning(f"Error eliminando operador {op_id}: {e}")
                messages.error(request, "No se puede eliminar el operador por restricciones de integridad.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
    
    try:
        lista = Operador.objects.select_related('organizacion', 'federacion').all().order_by('-fecha_registro')
        if q:
            lista = lista.filter(
                Q(organizacion__nombre__icontains=q) | 
                Q(federacion__nombre__icontains=q)
            )

        paginator = Paginator(lista, 20)
        registros = paginator.get_page(request.GET.get('page'))
    except DatabaseError as e:
        logger.error(f"Error consultando lista de operadores: {e}")
        messages.error(request, "Error al cargar la lista de operadores.")
        registros = []

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': NuevoOperadorForm(),
    }
    return render(request, 'gestion/gestion_operadores.html', contexto)


# ==========================================
# VISTA: MARCAS DE VEHÍCULOS
# ==========================================
@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def gestion_marcas(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        registro_id = request.POST.get('registro_id')
        marca = get_object_or_404(MarcaVehiculo, id=registro_id)

        if 'submit_editar' in request.POST:
            form = MarcaVehiculoForm(request.POST, instance=marca)
            if form.is_valid():
                try:
                    form.save()
                    messages.success(request, "Marca actualizada correctamente.")
                except Exception as e:
                    logger.error(f"Error editando marca {registro_id}: {e}")
                    messages.error(request, "Error interno al actualizar la marca.")
            else:
                messages.error(request, "Verifica los datos ingresados.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            try:
                marca.delete()
                messages.success(request, "Marca eliminada.")
            except Exception as e:
                logger.warning(f"Error eliminando marca ligada a vehículos: {e}")
                messages.error(request, "No se puede eliminar porque está en uso por un Vehículo.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
    
    try:
        lista = MarcaVehiculo.objects.all().order_by('-fecha_registro')
        if q:
            lista = lista.filter(nombre__icontains=q)

        paginator = Paginator(lista, 20)
        registros = paginator.get_page(request.GET.get('page'))
    except DatabaseError as e:
        logger.error(f"Error consultando marcas: {e}")
        registros = []

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': MarcaVehiculoForm(),
        'titulo': 'Marcas de Vehículos',
        'icono': 'fa-tags',
        'campo_mostrar': 'nombre' 
    }
    return render(request, 'gestion/gestion_parametros_vehiculo.html', contexto)

# ==========================================
# VISTA: TIPOS DE VEHÍCULOS
# ==========================================
@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def gestion_tipos(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        registro_id = request.POST.get('registro_id')
        tipo_vehiculo = get_object_or_404(TipoVehiculo, id=registro_id)

        if 'submit_editar' in request.POST:
            form = TipoVehiculoForm(request.POST, instance=tipo_vehiculo)
            if form.is_valid():
                try:
                    form.save()
                    messages.success(request, "Tipo actualizado correctamente.")
                except Exception as e:
                    logger.error(f"Error actualizando tipo vehículo {registro_id}: {e}")
                    messages.error(request, "Error del servidor.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            try:
                tipo_vehiculo.delete()
                messages.success(request, "Tipo eliminado.")
            except Exception as e:
                logger.warning(f"Error eliminando tipo en uso: {e}")
                messages.error(request, "No se puede eliminar porque está en uso por un Vehículo.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
    
    try:
        lista = TipoVehiculo.objects.all().order_by('-fecha_registro')
        if q:
            lista = lista.filter(tipo__icontains=q)

        paginator = Paginator(lista, 20)
        registros = paginator.get_page(request.GET.get('page'))
    except DatabaseError as e:
        logger.error(f"Error consultando tipos: {e}")
        registros = []

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': TipoVehiculoForm(),
        'titulo': 'Tipos de Vehículos',
        'icono': 'fa-car-side',
        'campo_mostrar': 'tipo'
    }
    return render(request, 'gestion/gestion_parametros_vehiculo.html', contexto)

# ==========================================
# VISTA: VEHÍCULOS
# ==========================================
@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def gestion_vehiculos(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        registro_id = request.POST.get('registro_id')
        vehiculo = get_object_or_404(Vehiculo, id=registro_id)

        try:
            if 'submit_editar' in request.POST:
                form = EditarVehiculoForm(request.POST, instance=vehiculo)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Vehículo actualizado correctamente.")
                else:
                    messages.error(request, "Error al actualizar. Revisa los datos.")
                return redirect(request.path)

            elif 'submit_eliminar' in request.POST:
                vehiculo.delete()
                messages.success(request, "Vehículo eliminado.")
                return redirect(request.path)
        except Exception as e:
            logger.error(f"Error procesando vehículo {registro_id}: {e}")
            messages.error(request, "Ocurrió un error en el servidor.")

    q = request.GET.get('q', '').strip()
    
    try:
        lista = Vehiculo.objects.select_related('afiliado', 'marca', 'tipo').all().order_by('-fecha_registro')
        if q:
            lista = lista.filter(
                Q(placa__icontains=q) | 
                Q(chasis__icontains=q) |
                Q(propietario__icontains=q) |
                Q(afiliado__nombre_completo__icontains=q)
            )

        paginator = Paginator(lista, 20)
        registros = paginator.get_page(request.GET.get('page'))
    except DatabaseError as e:
        logger.error(f"Error consultando vehículos: {e}")
        registros = []

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': EditarVehiculoForm(),
    }
    return render(request, 'gestion/gestion_vehiculos.html', contexto)

# ==========================================
# VISTA: TRÁMITES
# ==========================================
@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def gestion_tramites(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        try:
            if 'submit_editar_tramite' in request.POST:
                tramite = get_object_or_404(Tramite, id=request.POST.get('tramite_id'))
                form = EditarTramiteAdminForm(request.POST, instance=tramite)
                if form.is_valid():
                    form.save()
                    messages.success(request, f"Trámite N° {tramite.numero} actualizado.")
                else:
                    messages.error(request, "Error al actualizar el trámite.")
                return redirect(request.path)

            elif 'submit_eliminar_tramite' in request.POST:
                tramite = get_object_or_404(Tramite, id=request.POST.get('tramite_id'))
                numero = tramite.numero
                tramite.delete()
                messages.success(request, f"Trámite N° {numero} eliminado correctamente.")
                return redirect(request.path)

            elif 'submit_editar_deposito' in request.POST:
                deposito = get_object_or_404(Deposito, id=request.POST.get('deposito_id'))
                form = DepositoForm(request.POST, instance=deposito)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Depósito actualizado.")
                else:
                    messages.error(request, "Error al actualizar el depósito.")
                return redirect(request.path)

            elif 'submit_eliminar_deposito' in request.POST:
                deposito = get_object_or_404(Deposito, id=request.POST.get('deposito_id'))
                deposito.delete()
                messages.success(request, "Depósito eliminado correctamente.")
                return redirect(request.path)
        except Exception as e:
            logger.error(f"Error administrativo en trámites: {e}")
            messages.error(request, "Error del servidor procesando el trámite/depósito.")

    q = request.GET.get('q', '').strip()
    
    try:
        lista = Tramite.objects.select_related('usuario', 'operador__organizacion', 'operador__federacion')\
                               .prefetch_related('deposito_tramite')\
                               .all().order_by('-fecha_registro')
        if q:
            lista = lista.filter(
                Q(numero__icontains=q) | 
                Q(usuario__username__icontains=q) |
                Q(operador__organizacion__nombre__icontains=q)
            )

        paginator = Paginator(lista, 20)
        registros = paginator.get_page(request.GET.get('page'))
    except DatabaseError as e:
        logger.error(f"Error en consulta listando trámites: {e}")
        registros = []

    contexto = {
        'registros': registros,
        'q': q,
        'form_tramite': EditarTramiteAdminForm(),
        'form_deposito': DepositoForm(),
    }
    return render(request, 'gestion/gestion_tramites.html', contexto)

# ==========================================
# VISTA: TARJETAS DE OPERACIÓN
# ==========================================
@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def gestion_tarjetas(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        try:
            if 'submit_editar' in request.POST:
                tarjeta = get_object_or_404(TarjetaDeOperacion, id=request.POST.get('registro_id'))
                form = EditarTarjetaForm(request.POST, instance=tarjeta)
                if form.is_valid():
                    form.save()
                    messages.success(request, f"Tarjeta asociada al Trámite N° {tarjeta.tramite.numero} actualizada.")
                else:
                    messages.error(request, "Error al actualizar la tarjeta. Revisa los datos.")
                return redirect(request.path)

            elif 'submit_eliminar' in request.POST:
                tarjeta = get_object_or_404(TarjetaDeOperacion, id=request.POST.get('registro_id'))
                tramite_num = tarjeta.tramite.numero
                tarjeta.delete()
                messages.success(request, f"Tarjeta del Trámite N° {tramite_num} eliminada.")
                return redirect(request.path)
        except Exception as e:
            logger.error(f"Error gestionando tarjeta de operación: {e}")
            messages.error(request, "Error del sistema al procesar la tarjeta.")

    q = request.GET.get('q', '').strip()
    
    try:
        lista = TarjetaDeOperacion.objects.select_related(
            'tramite', 'operador__organizacion', 'afiliado', 'vehiculo'
        ).all().order_by('-fecha_registro')
        
        if q:
            lista = lista.filter(
                Q(tramite__numero__icontains=q) | 
                Q(afiliado__nombre_completo__icontains=q) |
                Q(vehiculo__placa__icontains=q) |
                Q(licencia__icontains=q) |
                Q(operador__organizacion__nombre__icontains=q)
            )

        paginator = Paginator(lista, 20)
        registros = paginator.get_page(request.GET.get('page'))
    except DatabaseError as e:
        logger.error(f"Error listando tarjetas: {e}")
        registros = []

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': EditarTarjetaForm(),
    }
    return render(request, 'gestion/gestion_tarjetas.html', contexto)

# ==========================================
# REPORTES Y EXPORTACIÓN
# ==========================================
@login_required
@user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def generar_reporte_pdf(request: HttpRequest) -> HttpResponse:
    try:
        # Diccionario para agrupar todo por mes ("YYYY-MM")
        reporte_por_mes = defaultdict(lambda: {
            'afiliados': [], 'operadores': [], 'vehiculos': [], 
            'tramites': [], 'tarjetas': [], 'logs': []
        })

        # 1. Obtener y agrupar Afiliados
        for a in Afiliado.objects.all().order_by('-fecha_registro'):
            mes = a.fecha_registro.strftime('%Y-%m')
            reporte_por_mes[mes]['afiliados'].append(a)

        # 2. Obtener y agrupar Operadores (Optimizados con select_related)
        for o in Operador.objects.select_related('organizacion', 'federacion').all().order_by('-fecha_registro'):
            mes = o.fecha_registro.strftime('%Y-%m')
            reporte_por_mes[mes]['operadores'].append(o)

        # 3. Obtener y agrupar Vehículos
        for v in Vehiculo.objects.select_related('marca', 'tipo').all().order_by('-fecha_registro'):
            mes = v.fecha_registro.strftime('%Y-%m')
            reporte_por_mes[mes]['vehiculos'].append(v)

        # 4. Obtener y agrupar Trámites
        for t in Tramite.objects.select_related('usuario', 'operador').all().order_by('-fecha_registro'):
            mes = t.fecha_registro.strftime('%Y-%m')
            reporte_por_mes[mes]['tramites'].append(t)

        # 5. Obtener y agrupar Tarjetas
        for tj in TarjetaDeOperacion.objects.select_related('tramite', 'vehiculo').all().order_by('-fecha_registro'):
            mes = tj.fecha_registro.strftime('%Y-%m')
            reporte_por_mes[mes]['tarjetas'].append(tj)

        # 6. Obtener y agrupar Logs (Auditoría)
        for log in LogEntry.objects.select_related('actor', 'content_type').all().order_by('-timestamp'):
            mes = log.timestamp.strftime('%Y-%m')
            reporte_por_mes[mes]['logs'].append(log)

        # Ordenar los meses del más reciente al más antiguo
        meses_ordenados = sorted(reporte_por_mes.items(), key=lambda x: x[0], reverse=True)

        context = {
            'meses_ordenados': meses_ordenados,
        }

        template = get_template('gestion/reporte_pdf.html')
        html = template.render(context)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="Reporte_General_Sistema.pdf"'

        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            logger.error(f"Error generando reporte global PDF: {pisa_status.err}")
            messages.error(request, "Error de la librería PDF al renderizar el reporte.")
            return redirect('gestion:historial_list')
            
        return response
        
    except Exception as e:
        logger.error(f"Error crítico construyendo reporte PDF: {e}")
        messages.error(request, "Ocurrió un problema interno al recopilar los datos para el reporte.")
        return redirect('gestion:historial_list')