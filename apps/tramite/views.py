from .models import Tramite, Deposito
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from apps.tramite.forms import NuevoTramiteForm, InformeTecnicoForm, InformeAndResolucionForm, DepositoForm
from apps.usuario.permisos import es_admin, es_superadmin, es_usuario_normal
from django.template.loader import get_template
from apps.tarjeta_de_operacion.forms import TarjetaDeOperacionForm
from apps.tarjeta_de_operacion.models import TarjetaDeOperacion
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
import qrcode
import io
import base64
from django.http import JsonResponse
from apps.afiliado.models import Afiliado
from apps.vehiculo.models import Vehiculo
from apps.afiliado.forms import NuevoAfiliadoForm
from apps.operador.forms import NuevoOperadorForm
from apps.vehiculo.forms import NuevoVehiculoForm, TipoVehiculoForm, MarcaVehiculoForm
from django.db import transaction
from apps.tarjeta_de_operacion.forms import EditarTarjetaForm

def vista_completa_tramite(request, numero):
    tramite = get_object_or_404(Tramite, numero=numero)
    tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite)
    depositos = Deposito.objects.filter(tramite=tramite)
    if request.method == 'POST':
        if 'btn_inf_tecnico' in request.POST:
            form_informe_tecnico = InformeTecnicoForm(request.POST, request.FILES, instance=tramite, prefix='infTecnico')
            if form_informe_tecnico.is_valid():
                form_informe_tecnico.save()
                return redirect('tramite:detalle_tramite', numero=tramite.numero)
        
        if 'btn_marcaV' in request.POST:
            form_marcaVehiculo = MarcaVehiculoForm(request.POST, prefix='marcaV')
            if form_marcaVehiculo.is_valid():
                form_marcaVehiculo.save()
                return redirect('tramite:detalle_tramite', numero=tramite.numero)
        if 'btn_tipoV' in request.POST:
            form_tipoVehiculo = TipoVehiculoForm(request.POST, prefix='tipoV')
            if form_tipoVehiculo.is_valid():
                form_tipoVehiculo.save()
                return redirect('tramite:detalle_tramite', numero=tramite.numero)
        
        if 'btn_inf_res' in request.POST:
            form_informe_resolucion = InformeAndResolucionForm(request.POST, request.FILES, instance=tramite, prefix='informeAndResolucion')
            if form_informe_resolucion.is_valid():
                form_informe_resolucion.save()
                return redirect('tramite:detalle_tramite', numero=tramite.numero)
        if 'btn_deposito' in request.POST:
            form_deposito = DepositoForm(request.POST, prefix='deposito')
            if form_deposito.is_valid():
                deposito = form_deposito.save(commit=False)
                deposito.tramite = tramite
                tramite.deposito = True
                tramite.save()
                deposito.save()
                return redirect('tramite:detalle_tramite', numero=tramite.numero)
        if 'btn_tarjeta' in request.POST:
            form_afiliado = NuevoAfiliadoForm(request.POST, prefix='afiliado')
            form_vehiculo = NuevoVehiculoForm(request.POST, prefix='vehiculo')
            if form_afiliado.is_valid() and form_vehiculo.is_valid():
                nombre_ingresado = form_afiliado.cleaned_data.get('nombre_completo')
                afiliado, created = Afiliado.objects.get_or_create(
                    nombre_completo=nombre_ingresado,
                    defaults={'operador': tramite.operador}
                )
                vehiculo = form_vehiculo.save(commit=False)
                if not vehiculo.propietario:
                    vehiculo.propietario = afiliado.nombre_completo
                vehiculo.afiliado = afiliado
                vehiculo.save()
                TarjetaDeOperacion.objects.create(
                    tramite=tramite,
                    operador=tramite.operador,
                    afiliado=afiliado,
                    vehiculo=vehiculo,
                    ruta=tramite.rutas,
                    licencia=tramite.licencia,
                )
                return redirect('tramite:detalle_tramite', numero=tramite.numero)
    else:
        form_informe_tecnico = InformeTecnicoForm(instance=tramite, prefix='infTecnico')
        form_informe_resolucion = InformeAndResolucionForm(instance=tramite, prefix='informeAndResolucion')
        form_afiliado = NuevoAfiliadoForm(prefix='afiliado')
        form_vehiculo = NuevoVehiculoForm(prefix='vehiculo')
        form_deposito = DepositoForm(prefix='deposito')
        form_tipoVehiculo = TipoVehiculoForm(prefix='tipoV')
        form_marcaVehiculo = MarcaVehiculoForm(prefix='marcaV')
        afiliados_existentes = Afiliado.objects.all()


    contexto = {
        'depositos': depositos,
        'tramite': tramite,
        'tarjetas': tarjetas,
        'form_informe_resolucion': form_informe_resolucion,
        'form_informe_tecnico': form_informe_tecnico,
        'form_afiliado': form_afiliado,
        'form_vehiculo': form_vehiculo,
        'form_deposito': form_deposito,
        'form_tipoVehiculo': form_tipoVehiculo,
        'form_marcaVehiculo': form_marcaVehiculo,
        'afiliados_existentes': afiliados_existentes,
    }
    return render(request, 'tramite/vista_completa.html', contexto)


# ========== TRAMITE VIEWS ==========
@login_required()
@user_passes_test(es_usuario_normal)
def lista_tramites(request):
    # ==========================================
    # 1. MANEJO DE CREACIÓN VÍA AJAX (POST)
    # ==========================================
    if request.method == 'POST':
        # Pasamos request.FILES por si algún día agregas subida de documentos
        form = NuevoTramiteForm(request.POST, request.FILES) 
        if form.is_valid():
            nuevo_tramite = form.save()
            return JsonResponse({
                'success': True,
                'mensaje': 'Trámite creado correctamente.',
                # Si tu modelo tiene un campo autogenerado, puedes devolverlo:
                # 'numero_tramite': nuevo_tramite.numero_tramite 
            })
        else:
            # Devuelve los errores exactos del formulario para mostrarlos si es necesario
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    # ==========================================
    # 2. MANEJO DE LA LISTA Y FILTROS (GET)
    # ==========================================
    form = NuevoTramiteForm() # Instancia vacía para el modal
    tramites = Tramite.objects.all().order_by('-fecha_registro')

    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', 'todos')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    tipo = request.GET.get('tipo', 'todos')

    # Filtrar por coincidencia de texto (Input)
    if q:
        filtros = Q(usuario__username__icontains=q)
        if q.isdigit():
            filtros |= Q(numero_tramite__icontains=q)
        tramites = tramites.filter(filtros)

    # Filtrar por Estado
    if estado and estado != 'todos':
        tramites = tramites.filter(estado_tramite=estado)

    # Filtro por Tipo
    if tipo and tipo != 'todos':
        tramites = tramites.filter(tipo_tramite=tipo)

    # Filtrar por Rango de Fechas
    if fecha_inicio:
        tramites = tramites.filter(fecha_registro__date__gte=parse_date(fecha_inicio))
    if fecha_fin:
        tramites = tramites.filter(fecha_registro__date__lte=parse_date(fecha_fin))

    # Paginación
    paginator = Paginator(tramites, 5)
    page_number = request.GET.get('page')
    tramites_paginados = paginator.get_page(page_number)

    contexto = {
        'tramites': tramites_paginados, # Usamos la variable paginada
        'q': q,
        'estado_actual': estado,
        'tipo_actual': tipo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'form': form, # <-- IMPORTANTE: Pasamos el formulario al template
    }
    return render(request, 'tramite/lista.html', contexto)
# def lista_tramites(request):
#     form = NuevoTramiteForm()
#     tramites = Tramite.objects.all().order_by('-fecha_registro')

#     q = request.GET.get('q', '').strip()
#     estado = request.GET.get('estado', 'todos')
#     fecha_inicio = request.GET.get('fecha_inicio', '')
#     fecha_fin = request.GET.get('fecha_fin', '')
#     tipo = request.GET.get('tipo', 'todos')

#     # 2. Filtrar por coincidencia de texto (Input)
#     if q:
#         # Buscamos por usuario
#         filtros = Q(usuario__username__icontains=q)
#         # Si el usuario ingresó solo números, también buscamos por N° de trámite
#         if q.isdigit():
#             filtros |= Q(numero_tramite__icontains=q)
        
#         tramites = tramites.filter(filtros)

#     # 3. Filtrar por Estado (Validado, Pendiente, Observado)
#     if estado and estado != 'todos':
#         tramites = tramites.filter(estado_tramite=estado)

#     # Filtro por Tipo <-- Nueva lógica
#     if tipo and tipo != 'todos':
#         tramites = tramites.filter(tipo_tramite=tipo)

#     # 4. Filtrar por Rango de Fechas
#     if fecha_inicio:
#         tramites = tramites.filter(fecha_registro__date__gte=parse_date(fecha_inicio))
#     if fecha_fin:
#         tramites = tramites.filter(fecha_registro__date__lte=parse_date(fecha_fin))

#     paginator = Paginator(tramites, 5)
#     page_number = request.GET.get('page')
#     tramites = paginator.get_page(page_number)

#     # 5. Pasamos los filtros de vuelta al contexto para que los inputs no se borren al recargar
#     contexto = {
#         'tramites': tramites,
#         'q': q,
#         'estado_actual': estado,
#         'tipo_actual': tipo,
#         'fecha_inicio': fecha_inicio,
#         'fecha_fin': fecha_fin,
#         'form': form,
#     }
#     return render(request, 'tramite/lista.html', contexto)

def vista(request, numero):
    tramite = get_object_or_404(Tramite, numero=numero)
    tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).order_by('-fecha_registro')
    
    if request.method == 'POST':
        if 'btn_actualizar_tarjeta' in request.POST:
            tarjeta_id = request.POST.get('tarjeta_id')
            
            try:
                # 1. Recuperamos la tarjeta específica
                tarjeta_edit = TarjetaDeOperacion.objects.get(id=tarjeta_id)
                
                # 2. Reconstruimos los forms usando 'instance' (para saber qué actualizar) 
                # y el 'prefix' dinámico (para saber qué datos del POST agarrar)
                prefijo_vehiculo = f"vehiculo_{tarjeta_id}"
                prefijo_tarjeta = f"tarjeta_{tarjeta_id}"
                
                form_vehiculo_edit = NuevoVehiculoForm(
                    request.POST, 
                    instance=tarjeta_edit.vehiculo, 
                    prefix=prefijo_vehiculo
                )
                form_tarjeta_edit = EditarTarjetaForm(
                    request.POST, 
                    instance=tarjeta_edit, 
                    prefix=prefijo_tarjeta
                )
                
                # # 3. Validamos y guardamos (atomic evita que se guarde uno sí y otro no)
                # if form_vehiculo_edit.is_valid() and form_tarjeta_edit.is_valid():
                #     with transaction.atomic():
                #         form_vehiculo_edit.save()
                #         form_tarjeta_edit.save()
                    
                #     # Recargamos la vista para ver los cambios
                #     # Ojo: si la url de esta función es otra, cambiala aquí
                #     return redirect('tramite:vista', numero=tramite.numero) 
                # 3. Validamos y guardamos
                if form_vehiculo_edit.is_valid() and form_tarjeta_edit.is_valid():
                    with transaction.atomic():
                        vehiculo = form_vehiculo_edit.save(commit=False)
                        tarjeta = form_tarjeta_edit.save(commit=False)
                        
                        # --- MAGIA DEL AFILIADO ---
                        # Capturamos el texto que escribiste en el input
                        nombre_editado = form_tarjeta_edit.cleaned_data.get('nombre_afiliado')
                        
                        # Buscamos o creamos el afiliado con ese nombre
                        afiliado_obj, created = Afiliado.objects.get_or_create(
                            nombre_completo=nombre_editado,
                            defaults={'operador': tramite.operador} # Asigna operador si es nuevo
                        )
                        
                        # Asignamos este afiliado tanto a la tarjeta como al vehículo
                        tarjeta.afiliado = afiliado_obj
                        vehiculo.afiliado = afiliado_obj
                        
                        vehiculo.save()
                        tarjeta.save()
                    
                    return redirect('tramite:vista', numero=tramite.numero)
                else:
                    # Útil para depurar en consola si algo no guarda
                    print("Errores Vehiculo:", form_vehiculo_edit.errors)
                    print("Errores Tarjeta:", form_tarjeta_edit.errors)
                    
            except TarjetaDeOperacion.DoesNotExist:
                print("Error: La tarjeta no existe")
            except Exception as e:
                print(f"Error al actualizar la tarjeta: {e}")

    # --- PREPARACIÓN DE DATOS PARA EL TEMPLATE (MÉTODO GET Y FALLBACK) ---
    tarjetas_data = []
    
    for tarjeta in tarjetas:
        # Por cada tarjeta, creamos formularios pre-llenados con su información
        # Es CRÍTICO usar el mismo formato de prefix aquí para que el HTML coincida
        f_vehiculo = NuevoVehiculoForm(instance=tarjeta.vehiculo, prefix=f"vehiculo_{tarjeta.id}")
        f_tarjeta = EditarTarjetaForm(instance=tarjeta, prefix=f"tarjeta_{tarjeta.id}")
        
        # Empaquetamos todo en un diccionario
        tarjetas_data.append({
            'obj': tarjeta,
            'form_vehiculo': f_vehiculo,
            'form_tarjeta': f_tarjeta
        })
    
    contexto = {
        'tramite': tramite,
        'tarjetas': tarjetas, # Lo mantenemos por si lo usas en un {% if tarjetas %}
        'tarjetas_data': tarjetas_data, # Esta es la lista que usará nuestro bucle en el HTML
    }
    
    return render(request, 'tramite/vista_tarjetas.html', contexto)

@login_required()
@user_passes_test(es_usuario_normal)
def detalle_tramite (request, numero):
    tramite = get_object_or_404(Tramite, numero=numero)
    tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).order_by('-fecha_registro')
    
    if request.method == 'POST':
        if 'btn_reporte' in request.POST:
            form_reporte = InformeTecnicoForm(request.POST, request.FILES, instance=tramite, prefix='reporte')
            if form_reporte.is_valid():
                guardado = form_reporte.save()
                return redirect('tramite:detalle_tramite', numero=tramite.numero)
                
        if 'btn_tarjeta' in request.POST and (request.user.rol == 'a' or request.user.rol == 'sa'):
            form_tarjeta = TarjetaDeOperacionForm(request.POST, prefix='tarjeta')
            
            # FILTRO POST: Es vital filtrar también aquí ANTES del is_valid() 
            # para que Django sepa que estos son los únicos valores permitidos.
            form_tarjeta.fields['afiliado'].queryset = Afiliado.objects.filter(operador=tramite.operador)
            form_tarjeta.fields['vehiculo'].queryset = Vehiculo.objects.filter(propietario__operador=tramite.operador)
            
            if form_tarjeta.is_valid():
                tarjeta_guardado = form_tarjeta.save(commit=False)
                tarjeta_guardado.tramite = tramite
                tarjeta_guardado.operador = tramite.operador
                tarjeta_guardado.save()
                return redirect('tramite:detalle_tramite', numero=tramite.numero)
                
        if 'btn_deposito' in request.POST and (request.user.rol == 'a' or request.user.rol == 'sa'):
            form_deposito = DepositoForm(request.POST, prefix='deposito')
            if form_deposito.is_valid():
                deposito_guardado = form_deposito.save(commit=False)
                deposito_guardado.tramite = tramite
                tramite.estado_deposito = True
                tramite.save()
                deposito_guardado.save()
                return redirect('tramite:detalle_tramite', numero=tramite.numero)
    else:
        form_informe_tecnico = InformeTecnicoForm(prefix='infTecnico')
        form_informe_resolucion = InformeAndResolucionForm(prefix='informeAndResolucion')
        form_tarjeta = TarjetaDeOperacionForm(prefix='tarjeta')
        
        # -------------------------------------------------------------------
        # FILTRO GET: Aquí limitamos las opciones que se envían al template HTML
        # -------------------------------------------------------------------
        # 1. Solo afiliados que pertenecen al operador del trámite
        # form_tarjeta.fields['afiliado'].queryset = Afiliado.objects.filter(operador=tramite.operador)
        
        # 2. Solo vehículos cuyo propietario (afiliado) pertenece al operador del trámite
        # Usamos los "dobles guiones bajos" (__) para navegar a través de la relación de modelos
        # form_tarjeta.fields['vehiculo'].queryset = Vehiculo.objects.filter(propietario__operador=tramite.operador)
        # -------------------------------------------------------------------
        
        form_deposito = DepositoForm(prefix='deposito')
        
    contexto = {
        'tramite': tramite,
        'tarjetas': tarjetas,
        'n_tarjetas': tarjetas.count(),
        'form_tarjeta': form_tarjeta,
        'form_informe_tecnico': form_informe_tecnico,
        'form_informe_resolucion': form_informe_resolucion,
        'form_deposito': form_deposito,
    }
    return render(request, 'tramite/detalle.html', contexto)

@login_required()
@user_passes_test(es_admin)
def crear_tramite (request):
    if request.method == 'POST':
        form = NuevoTramiteForm(request.POST, request.FILES)
        if form.is_valid():
            guardado = form.save()
            return redirect('tramite:lista_tramites')
    else:
        form = NuevoTramiteForm()
    contexto = {
        'form': form
    }
    return render(request, 'tramite/crear.html', contexto)

@login_required()
@user_passes_test(es_usuario_normal)
def editar_tramite (request, numero_tramite):
    tramite = get_object_or_404(Tramite, numero_tramite=numero_tramite)
    if request.method == 'POST':
        if 'btn_tramite' in request.POST and es_admin:
            form_tramite = InformeTecnicoForm(request.POST, instance=tramite, prefix='editar_tramite')
            if form_tramite.is_valid():
                guardado = form_tramite.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
        if 'btn_informe' in request.POST and es_admin:
            form_informe = InformeTecnicoForm(request.POST, instance=tramite, prefix='editar_informe')
            if form_informe.is_valid():
                guardado = form_informe.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
        if 'btn_reporte' in request.POST and es_usuario_normal:
            form_reporte = InformeTecnicoForm(request.POST, instance=tramite, prefix='editar_reporte')
            if form_reporte.is_valid():
                guardado = form_reporte.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
        if 'btn_estado' in request.POST and es_usuario_normal:
            form_estado = NuevoTramiteForm(request.POST, instance=tramite, prefix='editar_estado')
            if form_estado.is_valid():
                guardado = form_estado.save()
                return redirect('tramite:detalle_tramite', numero_tramite=tramite.numero_tramite)
    else:
        form_tramite = NuevoTramiteForm(prefix='editar_tramite')
        form_informe = InformeTecnicoForm(prefix='editar_informe')
        form_reporte = InformeTecnicoForm(prefix='editar_reporte')
        form_estado = NuevoTramiteForm(prefix='editar_estado')
    contexto = {
        'tramite': tramite,
        'form_tramite': form_tramite,
        'form_informe': form_informe,
        'form_reporte': form_reporte,
        'form_estado': form_estado,
    }
    return render(request, 'tramite/editar.html', contexto)

# ========== GENERACION DE PDFs ===========
@login_required()
@user_passes_test(es_admin)
def generar_pdf_tramite (request, numero_tramite):
    tramite = get_object_or_404(Tramite, numero_tramite=numero_tramite)
    tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).order_by('-fecha_registro')
    costo_total = sum(tarjeta.monto for tarjeta in tarjetas)
    for tarjeta in tarjetas:
        fecha_emision_str = tarjeta.fecha_emision.strftime('%d/%m/%Y') if tarjeta.fecha_emision else "Pendiente"
        valida_hasta_str = tarjeta.valida_hasta.strftime('%d/%m/%Y') if tarjeta.valida_hasta else "Pendiente"
        
        # Generar un texto estructurado y profesional para el escáner
        texto_qr = (
            "🏛️ G.A.D. POTOSI - SEC. TRANSPORTE\n"
            "----------------------------------\n"
            f"📄 TARJETA Nº: {tarjeta.id:06d}\n"
            f"🚗 PLACA: {tarjeta.vehiculo.placa}\n"
            f"🚙 VEHICULO: {tarjeta.vehiculo.marca.nombre} {tarjeta.vehiculo.modelo}\n"
            f"👤 TITULAR: {tarjeta.afiliado.nombre} {tarjeta.afiliado.apellido}\n"
            f"🏢 OPERADOR: {tarjeta.operador.nombre}\n"
            f"📌 SERVICIO: {tarjeta.get_tipo_tarjeta_display().upper()}\n"
            f"✅ EMISION: {fecha_emision_str}\n"
            f"⛔ VENCE: {valida_hasta_str}\n"
            "----------------------------------\n"
            f"🔍 Ref. Trámite: {tramite.numero_tramite}"
        )
        qr = qrcode.QRCode(
            version=1,  
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(texto_qr)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img_qr.save(buffer, format='PNG')
        imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        tarjeta.qr_data_uri = f"data:image/png;base64,{imagen_base64}"
        
    contexto = {
        'tramite': tramite,
        'tarjetas': tarjetas,
        'costo_total': costo_total,
    }
    template = get_template('pdf/tramite.html')
    template_render = template.render(contexto)
    response = HttpResponse(content_type = 'application/pdf')
    response['Content-Disposition'] = f'inline; filename="Tramite_{tramite.numero_tramite}.pdf"'
    pisa_status = pisa.CreatePDF(template_render, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF')
    return response