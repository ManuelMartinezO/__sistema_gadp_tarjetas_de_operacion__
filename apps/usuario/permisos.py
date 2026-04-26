def es_superadmin(user):
    return user.is_authenticated and user.rol == 'sa'

def es_admin(user):
    return user.is_authenticated and user.rol in ['sa', 'a']

def es_usuario_normal(user):
    return user.is_authenticated and user.rol in ['sa', 'a', 'u']