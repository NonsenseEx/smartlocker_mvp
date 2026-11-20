from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles_permitidos):
    """
    Decorador que verifica que el usuario autenticado tenga uno de los roles permitidos.
    Uso: @role_required('encargado', 'administrador')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.rol not in roles_permitidos:
                raise PermissionDenied(
                    "No tienes permisos para acceder a esta sección."
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator