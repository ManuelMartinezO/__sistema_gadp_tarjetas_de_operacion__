import io
import base64
import logging
import qrcode
from xhtml2pdf import pisa

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from django.db import transaction, DatabaseError
from django.contrib import messages

from .models import Tramite, Deposito
from apps.tramite.forms import NuevoTramiteForm, InformeTecnicoForm, InformeAndResolucionForm, DepositoForm
from apps.tarjeta_de_operacion.models import TarjetaDeOperacion
from apps.tarjeta_de_operacion.forms import EditarVistaTarjetaForm, TarjetaDeOperacionForm, EditarTarjetaForm
from apps.afiliado.models import Afiliado
from apps.vehiculo.models import Vehiculo
from apps.afiliado.forms import NuevoAfiliadoForm
from apps.operador.forms import NuevoOperadorForm
from apps.vehiculo.forms import NuevoVehiculoForm, TipoVehiculoForm, MarcaVehiculoForm
from apps.usuario.permisos import es_admin, es_superadmin, es_usuario_normal

logger = logging.getLogger(__name__)

@login_required
@user_passes_test(es_usuario_normal, login_url='/', redirect_field_name=None)
def vista_completa_tramite(request: HttpRequest, numero: str) -> HttpResponse:
    tramite = get_object_or_404(Tramite, numero=numero)
    tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).order_by('-fecha_registro')
    depositos = Deposito.objects.filter(tramite=tramite)
    
    if request.method == 'POST':
        try:
            if 'btn_inf_tecnico' in request.POST:
                form = InformeTecnicoForm(request.POST, request.FILES, instance=tramite, prefix='infTecnico')
                if form.is_valid():
                    form.save()
                    messages.success(request, "Informe técnico guardado correctamente.")
                    return redirect('tramite:detalle_tramite', numero=tramite.numero)
            
            elif 'btn_marcaV' in request.POST:
                form = MarcaVehiculoForm(request.POST, prefix='marcaV')
                if form.is_valid():
                    form.save()
                    messages.success(request, "Marca de vehículo registrada.")
                    return redirect('tramite:detalle_tramite', numero=tramite.numero)
                    
            elif 'btn_tipoV' in request.POST:
                form = TipoVehiculoForm(request.POST, prefix='tipoV')
                if form.is_valid():
                    form.save()
                    messages.success(request, "Tipo de vehículo registrado.")
                    return redirect('tramite:detalle_tramite', numero=tramite.numero)
            
            elif 'btn_inf_res' in request.POST:
                form = InformeAndResolucionForm(request.POST, request.FILES, instance=tramite, prefix='informeAndResolucion')
                if form.is_valid():
                    form.save()
                    messages.success(request, "Informe y Resolución guardados correctamente.")
                    return redirect('tramite:detalle_tramite', numero=tramite.numero)
                    
            elif 'btn_deposito' in request.POST:
                form = DepositoForm(request.POST, prefix='deposito')
                if form.is_valid():
                    with transaction.atomic():
                        deposito = form.save(commit=False)
                        deposito.tramite = tramite
                        deposito.save()
                        tramite.deposito = True
                        tramite.save()
                    messages.success(request, "Depósito registrado exitosamente.")
                    return redirect('tramite:detalle_tramite', numero=tramite.numero)
                    
            elif 'btn_tarjeta' in request.POST:
                # 1. Extraemos los identificadores únicos directamente del POST.
                # Usamos la sintaxis 'prefijo-nombre_campo' porque instancias los forms con prefix
                nombre_ingresado = request.POST.get('afiliado-nombre_completo')
                placa_ingresada = request.POST.get('vehiculo-placa')
                
                # 2. Buscamos si ya existen en la base de datos
                instancia_afiliado = Afiliado.objects.filter(nombre_completo=nombre_ingresado).first()
                instancia_vehiculo = Vehiculo.objects.filter(placa=placa_ingresada).first()
                
                # 3. Instanciamos los formularios. 
                # MAGIA: Al pasarle 'instance', si el objeto existe, Django lo actualiza sin dar error unique.
                # Si 'instance' es None, Django sabe que debe validar y crear uno nuevo.
                form_afiliado = NuevoAfiliadoForm(request.POST, prefix='afiliado', instance=instancia_afiliado)
                form_vehiculo = NuevoVehiculoForm(request.POST, prefix='vehiculo', instance=instancia_vehiculo)
                
                if form_afiliado.is_valid() and form_vehiculo.is_valid():
                    with transaction.atomic():
                        # Guardamos/Actualizamos el afiliado
                        afiliado = form_afiliado.save(commit=False)
                        if not afiliado.id:  # Si es nuevo, le asignamos el operador del trámite
                            afiliado.operador = tramite.operador
                        afiliado.save()
                        
                        # Guardamos/Actualizamos el vehículo
                        vehiculo = form_vehiculo.save(commit=False)
                        if not vehiculo.propietario:
                            vehiculo.propietario = afiliado.nombre_completo
                        
                        # Relacionamos el vehículo con el afiliado
                        vehiculo.afiliado = afiliado
                        vehiculo.save()
                        
                        # 4. Creamos la tarjeta de operación vinculando todo
                        TarjetaDeOperacion.objects.create(
                            tramite=tramite,
                            operador=tramite.operador,
                            afiliado=afiliado,
                            vehiculo=vehiculo,
                            ruta=tramite.rutas,
                            licencia=tramite.licencia,
                        )
                        
                    messages.success(request, "Tarjeta de operación generada y vinculada exitosamente.")
                    return redirect('tramite:detalle_tramite', numero=tramite.numero)
                    
                else:
                    # Capturamos por qué falló y mandamos el error
                    for campo, errores in form_vehiculo.errors.items():
                        for error in errores:
                            messages.error(request, f"Error en Vehículo: {error}")
                            
                    for campo, errores in form_afiliado.errors.items():
                        for error in errores:
                            messages.error(request, f"Error en Afiliado: {error}")
                    
        except Exception as e:
            logger.error(f"Error en vista_completa_tramite ({numero}): {e}")
            messages.error(request, "Ocurrió un error inesperado al procesar la solicitud.")

    form_informe_tecnico = InformeTecnicoForm(instance=tramite, prefix='infTecnico')
    form_informe_resolucion = InformeAndResolucionForm(prefix='informeAndResolucion')
    form_afiliado = NuevoAfiliadoForm(prefix='afiliado')
    form_vehiculo = NuevoVehiculoForm(prefix='vehiculo')
    form_deposito = DepositoForm(prefix='deposito')
    form_tipoVehiculo = TipoVehiculoForm(prefix='tipoV')
    form_marcaVehiculo = MarcaVehiculoForm(prefix='marcaV')
    afiliados_existentes = Afiliado.objects.all()
    vehiculos_existentes = Vehiculo.objects.all()

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
        'vehiculos_existentes': vehiculos_existentes,
    }
    return render(request, 'tramite/vista_completa.html', contexto)

@login_required
@user_passes_test(es_usuario_normal, login_url='/', redirect_field_name=None)
def lista_tramites(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = NuevoTramiteForm(request.POST, request.FILES) 
        if form.is_valid():
            try:
                form.save()
                return JsonResponse({'success': True, 'mensaje': 'Trámite creado.'})
            except Exception as e:
                logger.error(f"Error creando trámite via AJAX: {e}")
                return JsonResponse({'success': False, 'mensaje': 'Error en servidor.'}, status=500)
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    form = NuevoTramiteForm() 
    tramites = Tramite.objects.all().order_by('-fecha_registro')

    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', 'todos')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    tipo = request.GET.get('tipo', 'todos')

    try:
        if q:
            filtros = Q(usuario__username__icontains=q)
            if q.isdigit():
                filtros |= Q(numero__icontains=q)
            tramites = tramites.filter(filtros)

        if estado and estado != 'todos':
            tramites = tramites.filter(estado=estado)

        if tipo and tipo != 'todos':
            tramites = tramites.filter(tipo=tipo)

        if fecha_inicio:
            tramites = tramites.filter(fecha_registro__date__gte=parse_date(fecha_inicio))
            
        if fecha_fin:
            tramites = tramites.filter(fecha_registro__date__lte=parse_date(fecha_fin))

        paginator = Paginator(tramites, 10)
        page_number = request.GET.get('page')
        tramites_paginados = paginator.get_page(page_number)
        
    except DatabaseError as e:
        logger.error(f"Error de DB listando trámites: {e}")
        messages.error(request, "Ocurrió un problema al cargar los trámites.")
        tramites_paginados = []

    contexto = {
        'tramites': tramites_paginados, 
        'q': q,
        'estado_actual': estado,
        'tipo_actual': tipo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'form': form, 
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'GET':
        return render(request, 'tramite/parcial_tabla.html', contexto)

    return render(request, 'tramite/lista.html', contexto)

@login_required
@user_passes_test(es_usuario_normal, login_url='/', redirect_field_name=None)
def vista(request: HttpRequest, numero: str) -> HttpResponse:
    tramite = get_object_or_404(Tramite, numero=numero)
    tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).order_by('-fecha_registro')
    
    if request.method == 'POST':
        if 'btn_actualizar_tarjeta' in request.POST:
            tarjeta_id = request.POST.get('tarjeta_id')
            
            try:
                # Usamos select_related para traer la tarjeta, el vehículo y el afiliado de un solo golpe
                tarjeta_edit = TarjetaDeOperacion.objects.select_related('vehiculo', 'afiliado').get(id=tarjeta_id)
                prefijo_vehiculo = f"vehiculo_{tarjeta_id}"
                prefijo_tarjeta = f"tarjeta_{tarjeta_id}"
                
                # Instanciamos los formularios con las instancias que ya están vinculadas
                form_vehiculo_edit = NuevoVehiculoForm(request.POST, instance=tarjeta_edit.vehiculo, prefix=prefijo_vehiculo)
                form_tarjeta_edit = EditarVistaTarjetaForm(request.POST, instance=tarjeta_edit, prefix=prefijo_tarjeta)
                
                if form_vehiculo_edit.is_valid() and form_tarjeta_edit.is_valid():
                    with transaction.atomic():
                        # 1. Se actualizan los datos del vehículo existente
                        vehiculo = form_vehiculo_edit.save()
                        
                        # 2. Se actualizan los datos de la tarjeta existente
                        tarjeta = form_tarjeta_edit.save(commit=False)
                        
                        # 3. Se actualiza únicamente el nombre del afiliado ya vinculado
                        nombre_editado = form_tarjeta_edit.cleaned_data.get('nombre_afiliado')
                        if nombre_editado:
                            afiliado = tarjeta.afiliado
                            afiliado.nombre_completo = nombre_editado
                            afiliado.save()
                            
                            # Sincronizamos el propietario del vehículo para que coincida
                            vehiculo.propietario = nombre_editado
                            vehiculo.save()
                        
                        tarjeta.save()
                        
                    messages.success(request, "Tarjeta y datos asociados actualizados correctamente.")
                    return redirect('tramite:vista', numero=tramite.numero) 
                    
                else:
                    # Reporte de errores detallado si la validación falla
                    for campo, errores in form_vehiculo_edit.errors.items():
                        for error in errores:
                            messages.error(request, f"Error en Vehículo (Tarjeta {tarjeta_id}): {error}")
                            
                    for campo, errores in form_tarjeta_edit.errors.items():
                        for error in errores:
                            messages.error(request, f"Error en Tarjeta ({tarjeta_id}) - Campo '{campo}': {error}")
                            
            except TarjetaDeOperacion.DoesNotExist:
                logger.warning(f"Intento de actualizar tarjeta inexistente: {tarjeta_id}")
                messages.error(request, "La tarjeta especificada no existe.")
            except Exception as e:
                logger.error(f"Error actualizando tarjeta {tarjeta_id}: {e}")
                messages.error(request, "Error interno al guardar los datos.")

    tarjetas_data = []
    for tarjeta in tarjetas:
        f_vehiculo = NuevoVehiculoForm(instance=tarjeta.vehiculo, prefix=f"vehiculo_{tarjeta.id}")
        f_tarjeta = EditarTarjetaForm(instance=tarjeta, prefix=f"tarjeta_{tarjeta.id}")
        tarjetas_data.append({
            'obj': tarjeta,
            'form_vehiculo': f_vehiculo,
            'form_tarjeta': f_tarjeta
        })
    
    contexto = {
        'tramite': tramite,
        'tarjetas': tarjetas,
        'tarjetas_data': tarjetas_data,
    }
    
    return render(request, 'tramite/vista_tarjetas.html', contexto)

@login_required
@user_passes_test(es_usuario_normal, login_url='/', redirect_field_name=None)
def detalle_tramite(request: HttpRequest, numero: str) -> HttpResponse:
    tramite = get_object_or_404(Tramite, numero=numero)
    tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).order_by('-fecha_registro')
    
    if request.method == 'POST':
        try:
            if 'btn_reporte' in request.POST:
                form = InformeTecnicoForm(request.POST, request.FILES, instance=tramite, prefix='reporte')
                if form.is_valid():
                    form.save()
                    messages.success(request, "Reporte técnico guardado con éxito.")
                    return redirect('tramite:detalle_tramite', numero=tramite.numero)
                    
            elif 'btn_tarjeta' in request.POST and request.user.rol in ['a', 'sa']:
                form = TarjetaDeOperacionForm(request.POST, prefix='tarjeta')
                if form.is_valid():
                    tarjeta = form.save(commit=False)
                    tarjeta.tramite = tramite
                    tarjeta.operador = tramite.operador
                    tarjeta.save()
                    messages.success(request, "Nueva tarjeta asignada al trámite.")
                    return redirect('tramite:detalle_tramite', numero=tramite.numero)
                    
            elif 'btn_deposito' in request.POST and request.user.rol in ['a', 'sa']:
                form = DepositoForm(request.POST, prefix='deposito')
                if form.is_valid():
                    with transaction.atomic():
                        deposito = form.save(commit=False)
                        deposito.tramite = tramite
                        deposito.save()
                        tramite.estado_deposito = True
                        tramite.save()
                    messages.success(request, "Depósito registrado.")
                    return redirect('tramite:detalle_tramite', numero=tramite.numero)
                    
        except Exception as e:
            logger.error(f"Error en detalle_tramite ({numero}): {e}")
            messages.error(request, "Ocurrió un error al procesar la operación.")

    form_informe_tecnico = InformeTecnicoForm(prefix='infTecnico')
    form_informe_resolucion = InformeAndResolucionForm(prefix='informeAndResolucion')
    form_tarjeta = TarjetaDeOperacionForm(prefix='tarjeta')
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

@login_required
@user_passes_test(es_admin, login_url='/', redirect_field_name=None)
def generar_pdf_tramite(request: HttpRequest, numero: str) -> HttpResponse:
    tramite = get_object_or_404(Tramite, numero=numero)
    tarjetas = TarjetaDeOperacion.objects.filter(tramite=tramite).order_by('-fecha_registro')
    costo_total = sum(tarjeta.monto for tarjeta in tarjetas)
    
    for tarjeta in tarjetas:
        # Simplificación del texto del QR como dato de respaldo.
        texto_qr = (
            f"Ref. Trámite: {tramite.numero} - Tarjeta: {tarjeta.id}\n"
            f"PLACA: {tarjeta.vehiculo.placa}\n"
            f"MARCA: {tarjeta.vehiculo.marca.nombre}\n"
            f"MODELO: {tarjeta.vehiculo.modelo}\n"
            f"ESTADO: {tarjeta.get_estado_display()}\n"
            f"EMITIDA: {tarjeta.fecha_emision}\n"
            f"VENCE: {tarjeta.valida_hasta}\n"
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
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Tramite_{tramite.numero}.pdf"'
    
    pisa_status = pisa.CreatePDF(template_render, dest=response)
    
    if pisa_status.err:
        logger.error(f"Error generando PDF para trámite {numero}: {pisa_status.err}")
        messages.error(request, "Error del motor al generar el documento PDF.")
        return redirect('tramite:detalle_tramite', numero=tramite.numero)
        
    return response