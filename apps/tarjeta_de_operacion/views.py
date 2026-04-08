from django.shortcuts import render, redirect, get_object_or_404
from .models import TarjetaDeOperacion
from .forms import TarjetaDeOperacionForm

from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
import io
import qrcode
import base64


def lista_tarjetas (request):
    tarjetas = TarjetaDeOperacion.objects.all()
    contexto = {
        'tarjetas': tarjetas
    }
    return render(request, 'tarjeta/lista.html', contexto)
    
def detalle_tarjeta (request, id_tarjeta):
    tarjeta = get_object_or_404(TarjetaDeOperacion, id=id_tarjeta)
    contexto = {
        'tarjeta': tarjeta,
    }
    return render(request, 'tarjeta/detalle.html', contexto)

def crear_tarjeta (request):
    if request.method == 'POST':
        form = TarjetaDeOperacionForm(request.POST)
        if form.is_valid():
            guardado = form.save()
            return redirect('tarjeta:lista_tarjetas')
    else:
        form = TarjetaDeOperacionForm()
    contexto = {
        'form': form,
    }
    return render(request, 'tarjeta/crear.html', contexto)


def generar_pdf_tarjeta (request, id_tarjeta):
    tarjeta = get_object_or_404(TarjetaDeOperacion, id=id_tarjeta)
    texto_qr = (
        f"PLACA: {tarjeta.vehiculo.placa}\n"
        f"MARCA: {tarjeta.vehiculo.marca}\n"
        f"MODELO: {tarjeta.vehiculo.modelo}\n"
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
    qr_data_uri = f"data:image/png;base64,{imagen_base64}"
    contexto = {
        'tarjeta': tarjeta,
        'qr_data_uri': qr_data_uri,
    }
    template = get_template('pdf/tarjeta.html')
    template_render = template.render(contexto)
    response = HttpResponse(content_type = 'application/pdf')
    response['Content-Disposition'] = f'inline; filename="Tarjeta_Vehiculo_{tarjeta.vehiculo.placa}.pdf"'
    pisa_status = pisa.CreatePDF(template_render, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF')
    return response
    