def es_superadmin(user):
    # Verifica que esté logueado y sea Super Administrador
    return user.is_authenticated and user.rol == 'sa'

def es_admin(user):
    # Asumimos que un 'sa' también puede ver lo de un 'a'
    return user.is_authenticated and user.rol in ['sa', 'a']

def es_usuario_normal(user):
    # Todos los logueados tienen al menos rol 'u'
    return user.is_authenticated and user.rol in ['sa', 'a', 'u']