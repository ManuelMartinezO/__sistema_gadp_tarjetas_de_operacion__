
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import HistorialAccion

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