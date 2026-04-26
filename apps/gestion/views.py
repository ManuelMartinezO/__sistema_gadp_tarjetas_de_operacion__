
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import HistorialAccion
from apps.usuario.forms import PerfilForm, UsuarioForm
from django.contrib.auth import login, logout
from django.db import transaction
from apps.usuario.permisos import es_admin, es_usuario_normal, es_superadmin
from apps.operador.models import Operador
from django.contrib import messages
from auditlog.models import LogEntry
from django.db.models import Q
# # Función auxiliar para el decorador: verifica si es superusuario
# def es_superadmin(user):
#     return user.is_superuser

def historial_list_view(request):
    # 1. Obtener todos los logs
    lista_logs = LogEntry.objects.select_related('actor', 'content_type').all()

    # 2. Capturar los parámetros de filtro específicos
    date_start = request.GET.get('date_start', '').strip()
    date_end = request.GET.get('date_end', '').strip()
    user_filter = request.GET.get('user', '').strip()
    ip_filter = request.GET.get('ip', '').strip()
    action_filter = request.GET.get('action', '').strip()
    module_filter = request.GET.get('module', '').strip()
    
    # 3. Aplicar los filtros condicionalmente
    if date_start:
        lista_logs = lista_logs.filter(timestamp__date__gte=date_start) # Mayor o igual a la fecha de inicio
    if date_end:
        lista_logs = lista_logs.filter(timestamp__date__lte=date_end)   # Menor o igual a la fecha de fin
    if user_filter:
        lista_logs = lista_logs.filter(actor__username__icontains=user_filter)
    if ip_filter:
        lista_logs = lista_logs.filter(remote_addr__icontains=ip_filter)
    if action_filter and action_filter in ['0', '1', '2']:
        lista_logs = lista_logs.filter(action=int(action_filter))
    if module_filter:
        lista_logs = lista_logs.filter(content_type__model__icontains=module_filter)

    # 4. Configurar paginación (20 registros)
    paginator = Paginator(lista_logs, 20)
    page_number = request.GET.get('page', 1)

    try:
        logs = paginator.page(page_number)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)

    # 5. Generar cadena de búsqueda para mantener filtros en la paginación
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


# 
# # Aplicamos el decorador para que solo los superadmins pasen de aquí
# @user_passes_test(es_superadmin)
# def historial_list_view(request):
#     # 1. Obtener todos los registros de la base de datos
#     # (Ya vienen ordenados del más reciente al más antiguo por la clase Meta del modelo)
#     lista_logs = HistorialAccion.objects.all()

#     # 2. Configurar el paginador (mostrar 20 registros por página)
#     paginator = Paginator(lista_logs, 20)

#     # 3. Capturar el número de página que el usuario pide en la URL (ej. /auditoria/?page=2)
#     # Si no hay parámetro 'page', por defecto será la página 1
#     page_number = request.GET.get('page', 1)

#     try:
#         # Intentar obtener los registros de esa página exacta
#         logs = paginator.page(page_number)
#     except PageNotAnInteger:
#         # Si alguien escribe letras en la URL (ej. ?page=hola), lo mandamos a la página 1
#         logs = paginator.page(1)
#     except EmptyPage:
#         # Si piden una página que no existe (ej. la 9999), les damos la última página válida
#         logs = paginator.page(paginator.num_pages)

#     # 4. Empaquetar los datos en un diccionario de contexto
#     context = {
#         'logs': logs,
#     }

#     # 5. Renderizar la plantilla enviando el contexto
#     return render(request, 'gestion/historial_list.html', context)

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
        form = PerfilForm(request.POST)
        if form.is_valid():
            operador = form.save()
            messages.success(request, f"Operador '{operador.nombre}' registrado con éxito.")
            return redirect('gestion:operador_list')
        else:
            messages.error(request, "Error al registrar. Verifique los datos.")
    else:
        form = PerfilForm()
        
    return render(request, 'gestion/operador_form.html', {'form': form, 'accion': 'Crear'})

# @login_required
# @user_passes_test(es_superadmin, login_url='/', redirect_field_name=None)
def editar_operador(request, pk):
    operador = get_object_or_404(Operador, pk=pk)
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=operador)
        if form.is_valid():
            form.save()
            messages.success(request, f"Operador '{operador.nombre}' actualizado correctamente.")
            return redirect('gestion:operador_list')
    else:
        form = PerfilForm(instance=operador)
        
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

from apps.afiliado.models import Afiliado
from apps.afiliado.forms import EditarAfiliadoForm

def gestion_admin_afiliados(request):
    if request.method == 'POST':
        afiliado_id = request.POST.get('afiliado_id')
        afiliado = get_object_or_404(Afiliado, id=afiliado_id)

        if 'submit_editar' in request.POST:
            form_edicion = EditarAfiliadoForm(request.POST, instance=afiliado)
            if form_edicion.is_valid():
                form_edicion.save()
                messages.success(request, f"El afiliado {afiliado.nombre_completo} ha sido actualizado correctamente.")
            else:
                messages.danger(request, "Error al actualizar el afiliado. Revisa los datos.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            nombre = afiliado.nombre_completo
            afiliado.delete()
            messages.success(request, f"El afiliado {nombre} fue eliminado definitivamente.")
            return redirect(request.path)

    # GET: Mostrar lista y Búsqueda
    q = request.GET.get('q', '').strip()
    afiliados_list = Afiliado.objects.select_related('operador').all().order_by('-fecha_registro')

    if q:
        afiliados_list = afiliados_list.filter(nombre_completo__icontains=q)

    # --- CAMBIO: Paginación a 20 registros ---
    paginator = Paginator(afiliados_list, 20)
    page_number = request.GET.get('page')
    afiliados = paginator.get_page(page_number)

    form_generico = EditarAfiliadoForm()

    contexto = {
        'afiliados': afiliados,
        'q': q,
        'form_generico': form_generico,
    }
    return render(request, 'gestion/gestion_afiliados.html', contexto)


from apps.operador.models import Federacion, Organizacion, Operador
from apps.operador.forms import NuevoOperadorForm, OrganizacionForm, FederacionForm

def gestion_organizaciones(request):
    if request.method == 'POST':
        org_id = request.POST.get('registro_id')
        organizacion = get_object_or_404(Organizacion, id=org_id)

        if 'submit_editar' in request.POST:
            form = OrganizacionForm(request.POST, instance=organizacion)
            if form.is_valid():
                form.save()
                messages.success(request, "Organización actualizada correctamente.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            # Ojo: Si la organización está ligada a un operador (on_delete=PROTECT),
            # Django lanzará un error. Podrías capturar el error RestrictedError aquí.
            try:
                organizacion.delete()
                messages.success(request, "Organización eliminada.")
            except Exception as e:
                messages.danger(request, "No se puede eliminar porque está en uso por un Operador.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
    lista = Organizacion.objects.all().order_by('-fecha_registro')
    if q:
        lista = lista.filter(nombre__icontains=q)

    paginator = Paginator(lista, 20)
    registros = paginator.get_page(request.GET.get('page'))

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
def gestion_federaciones(request):
    if request.method == 'POST':
        fed_id = request.POST.get('registro_id')
        federacion = get_object_or_404(Federacion, id=fed_id)

        if 'submit_editar' in request.POST:
            form = FederacionForm(request.POST, instance=federacion)
            if form.is_valid():
                form.save()
                messages.success(request, "Federación actualizada correctamente.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            try:
                federacion.delete()
                messages.success(request, "Federación eliminada.")
            except Exception as e:
                messages.danger(request, "No se puede eliminar porque está en uso.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
    lista = Federacion.objects.all().order_by('-fecha_registro')
    if q:
        lista = lista.filter(nombre__icontains=q)

    paginator = Paginator(lista, 20)
    registros = paginator.get_page(request.GET.get('page'))

    # Reutilizamos el mismo template de organizaciones porque tienen la misma estructura
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
def gestion_operadores(request):
    if request.method == 'POST':
        op_id = request.POST.get('registro_id')
        operador = get_object_or_404(Operador, id=op_id)

        if 'submit_editar' in request.POST:
            form = NuevoOperadorForm(request.POST, instance=operador)
            if form.is_valid():
                form.save()
                messages.success(request, "Operador actualizado.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            operador.delete()
            messages.success(request, "Operador eliminado.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
    lista = Operador.objects.select_related('organizacion', 'federacion').all().order_by('-fecha_registro')
    
    if q:
        lista = lista.filter(
            Q(organizacion__nombre__icontains=q) | 
            Q(federacion__nombre__icontains=q)
        )

    paginator = Paginator(lista, 20)
    registros = paginator.get_page(request.GET.get('page'))

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': NuevoOperadorForm(),
    }
    return render(request, 'gestion/gestion_operadores.html', contexto)

from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from apps.vehiculo.models import Vehiculo, MarcaVehiculo, TipoVehiculo
from apps.vehiculo.forms import EditarVehiculoForm, MarcaVehiculoForm, TipoVehiculoForm
from apps.tramite.models import Tramite, Deposito
from apps.tramite.forms import EditarTramiteAdminForm, DepositoForm


# ==========================================
# VISTA: MARCAS DE VEHÍCULO
# ==========================================
def gestion_marcas(request):
    if request.method == 'POST':
        registro_id = request.POST.get('registro_id')
        marca = get_object_or_404(MarcaVehiculo, id=registro_id)

        if 'submit_editar' in request.POST:
            form = MarcaVehiculoForm(request.POST, instance=marca)
            if form.is_valid():
                form.save()
                messages.success(request, "Marca actualizada correctamente.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            try:
                marca.delete()
                messages.success(request, "Marca eliminada.")
            except Exception:
                messages.danger(request, "No se puede eliminar porque está en uso por un Vehículo.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
    lista = MarcaVehiculo.objects.all().order_by('-fecha_registro')
    if q:
        lista = lista.filter(nombre__icontains=q)

    paginator = Paginator(lista, 20)
    registros = paginator.get_page(request.GET.get('page'))

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': MarcaVehiculoForm(),
        'titulo': 'Marcas de Vehículos',
        'icono': 'fa-tags',
        'campo_mostrar': 'nombre' # Le dice al template qué campo imprimir
    }
    return render(request, 'gestion/gestion_parametros_vehiculo.html', contexto)

# ==========================================
# VISTA: TIPOS DE VEHÍCULO
# ==========================================
def gestion_tipos(request):
    if request.method == 'POST':
        registro_id = request.POST.get('registro_id')
        tipo_vehiculo = get_object_or_404(TipoVehiculo, id=registro_id)

        if 'submit_editar' in request.POST:
            form = TipoVehiculoForm(request.POST, instance=tipo_vehiculo)
            if form.is_valid():
                form.save()
                messages.success(request, "Tipo actualizado correctamente.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            try:
                tipo_vehiculo.delete()
                messages.success(request, "Tipo eliminado.")
            except Exception:
                messages.danger(request, "No se puede eliminar porque está en uso por un Vehículo.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
    lista = TipoVehiculo.objects.all().order_by('-fecha_registro')
    if q:
        lista = lista.filter(tipo__icontains=q)

    paginator = Paginator(lista, 20)
    registros = paginator.get_page(request.GET.get('page'))

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': TipoVehiculoForm(),
        'titulo': 'Tipos de Vehículos',
        'icono': 'fa-car-side',
        'campo_mostrar': 'tipo'
    }
    # Reutilizamos el mismo template que para las Marcas
    return render(request, 'gestion/gestion_parametros_vehiculo.html', contexto)

# ==========================================
# VISTA: VEHÍCULOS (INVENTARIO GENERAL)
# ==========================================
def gestion_vehiculos(request):
    if request.method == 'POST':
        registro_id = request.POST.get('registro_id')
        vehiculo = get_object_or_404(Vehiculo, id=registro_id)

        if 'submit_editar' in request.POST:
            form = EditarVehiculoForm(request.POST, instance=vehiculo)
            if form.is_valid():
                form.save()
                messages.success(request, "Vehículo actualizado correctamente.")
            else:
                messages.danger(request, "Error al actualizar. Revisa los datos.")
            return redirect(request.path)

        elif 'submit_eliminar' in request.POST:
            vehiculo.delete()
            messages.success(request, "Vehículo eliminado.")
            return redirect(request.path)

    q = request.GET.get('q', '').strip()
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

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': EditarVehiculoForm(),
    }
    return render(request, 'gestion/gestion_vehiculos.html', contexto)


def gestion_tramites(request):
    # ==========================================
    # 1. PROCESAR ACCIONES (POST)
    # ==========================================
    if request.method == 'POST':
        
        # --- A) EDITAR TRÁMITE ---
        if 'submit_editar_tramite' in request.POST:
            tramite = get_object_or_404(Tramite, id=request.POST.get('tramite_id'))
            form = EditarTramiteAdminForm(request.POST, instance=tramite)
            if form.is_valid():
                form.save()
                messages.success(request, f"Trámite N° {tramite.numero} actualizado.")
            else:
                messages.danger(request, "Error al actualizar el trámite.")
            return redirect(request.path)

        # --- B) ELIMINAR TRÁMITE ---
        elif 'submit_eliminar_tramite' in request.POST:
            tramite = get_object_or_404(Tramite, id=request.POST.get('tramite_id'))
            numero = tramite.numero
            tramite.delete() # Esto eliminará en cascada sus depósitos (on_delete=CASCADE)
            messages.success(request, f"Trámite N° {numero} eliminado correctamente.")
            return redirect(request.path)

        # --- C) EDITAR DEPÓSITO ---
        elif 'submit_editar_deposito' in request.POST:
            deposito = get_object_or_404(Deposito, id=request.POST.get('deposito_id'))
            form = DepositoForm(request.POST, instance=deposito)
            if form.is_valid():
                form.save()
                messages.success(request, "Depósito actualizado.")
            else:
                messages.danger(request, "Error al actualizar el depósito.")
            return redirect(request.path)

        # --- D) ELIMINAR DEPÓSITO ---
        elif 'submit_eliminar_deposito' in request.POST:
            deposito = get_object_or_404(Deposito, id=request.POST.get('deposito_id'))
            deposito.delete()
            messages.success(request, "Depósito eliminado correctamente.")
            return redirect(request.path)

    # ==========================================
    # 2. MOSTRAR LISTA Y BÚSQUEDA (GET)
    # ==========================================
    q = request.GET.get('q', '').strip()
    
    # Pre-cargamos las relaciones ForeignKey y Reverse Foreign Key (depósitos)
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

    contexto = {
        'registros': registros,
        'q': q,
        'form_tramite': EditarTramiteAdminForm(),
        'form_deposito': DepositoForm(),
    }
    return render(request, 'gestion/gestion_tramites.html', contexto)
    

from apps.tarjeta_de_operacion.models import TarjetaDeOperacion
from apps.tarjeta_de_operacion.forms import EditarTarjetaForm

def gestion_tarjetas(request):
    # ==========================================
    # 1. PROCESAR ACCIONES (POST)
    # ==========================================
    if request.method == 'POST':
        
        # --- A) EDITAR ---
        if 'submit_editar' in request.POST:
            tarjeta = get_object_or_404(TarjetaDeOperacion, id=request.POST.get('registro_id'))
            form = EditarTarjetaForm(request.POST, instance=tarjeta)
            if form.is_valid():
                form.save()
                messages.success(request, f"Tarjeta asociada al Trámite N° {tarjeta.tramite.numero} actualizada.")
            else:
                messages.danger(request, "Error al actualizar la tarjeta. Revisa los datos.")
            return redirect(request.path)

        # --- B) ELIMINAR ---
        elif 'submit_eliminar' in request.POST:
            tarjeta = get_object_or_404(TarjetaDeOperacion, id=request.POST.get('registro_id'))
            tramite_num = tarjeta.tramite.numero
            tarjeta.delete()
            messages.success(request, f"Tarjeta del Trámite N° {tramite_num} eliminada.")
            return redirect(request.path)

    # ==========================================
    # 2. MOSTRAR LISTA Y BÚSQUEDA (GET)
    # ==========================================
    q = request.GET.get('q', '').strip()
    
    # Optimizamos las relaciones ForeignKey
    lista = TarjetaDeOperacion.objects.select_related(
        'tramite', 'operador__organizacion', 'afiliado', 'vehiculo'
    ).all().order_by('-fecha_registro')
    
    # Buscador potente en múltiples campos
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

    contexto = {
        'registros': registros,
        'q': q,
        'form_generico': EditarTarjetaForm(),
    }
    return render(request, 'gestion/gestion_tarjetas.html', contexto)


from collections import defaultdict
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def generar_reporte_pdf(request):
    # Diccionario para agrupar todo por mes ("YYYY-MM")
    # defaultdict nos permite crear la estructura automáticamente si el mes no existe aún
    reporte_por_mes = defaultdict(lambda: {
        'afiliados': [], 'operadores': [], 'vehiculos': [], 
        'tramites': [], 'tarjetas': [], 'logs': []
    })

    # 1. Obtener y agrupar Afiliados
    for a in Afiliado.objects.all().order_by('fecha_registro'):
        mes = a.fecha_registro.strftime('%Y-%m')
        reporte_por_mes[mes]['afiliados'].append(a)

    # 2. Obtener y agrupar Operadores
    for o in Operador.objects.select_related('organizacion', 'federacion').all().order_by('fecha_registro'):
        mes = o.fecha_registro.strftime('%Y-%m')
        reporte_por_mes[mes]['operadores'].append(o)

    # 3. Obtener y agrupar Vehículos
    for v in Vehiculo.objects.select_related('marca', 'tipo').all().order_by('fecha_registro'):
        mes = v.fecha_registro.strftime('%Y-%m')
        reporte_por_mes[mes]['vehiculos'].append(v)

    # 4. Obtener y agrupar Trámites
    for t in Tramite.objects.select_related('usuario', 'operador').all().order_by('fecha_registro'):
        mes = t.fecha_registro.strftime('%Y-%m')
        reporte_por_mes[mes]['tramites'].append(t)

    # 5. Obtener y agrupar Tarjetas
    for tj in TarjetaDeOperacion.objects.select_related('tramite', 'vehiculo').all().order_by('fecha_registro'):
        mes = tj.fecha_registro.strftime('%Y-%m')
        reporte_por_mes[mes]['tarjetas'].append(tj)

    # 6. Obtener y agrupar Logs (Auditoría)
    for log in LogEntry.objects.select_related('actor', 'content_type').all().order_by('timestamp'):
        mes = log.timestamp.strftime('%Y-%m')
        reporte_por_mes[mes]['logs'].append(log)

    # Ordenar los meses del más reciente al más antiguo
    meses_ordenados = sorted(reporte_por_mes.items(), key=lambda x: x[0], reverse=True)

    # Generar el contexto para el template
    context = {
        'meses_ordenados': meses_ordenados,
    }

    # Renderizar el HTML
    template = get_template('gestion/reporte_pdf.html')
    html = template.render(context)

    # Crear la respuesta HTTP como PDF
    response = HttpResponse(content_type='application/pdf')
    
    # ¡AQUÍ ESTÁ EL CAMBIO! 
    # 'inline' le dice al navegador que intente abrirlo en su visor de PDF interno.
    response['Content-Disposition'] = 'inline; filename="Reporte_General_Sistema.pdf"'

    # Convertir el HTML a PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Tuvimos algunos errores al generar el PDF <pre>' + html + '</pre>')
    
    return response