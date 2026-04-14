import threading

# Espacio en memoria para el hilo actual
_thread_locals = threading.local()

def get_current_request():
    """Devuelve el request actual desde cualquier parte del código."""
    return getattr(_thread_locals, 'request', None)

def get_current_user():
    """Devuelve el usuario actual desde cualquier parte del código."""
    request = get_current_request()
    if request:
        return getattr(request, 'user', None)
    return None

class RequestMiddleware:
    """Middleware para guardar el request en la memoria local del hilo."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        return response