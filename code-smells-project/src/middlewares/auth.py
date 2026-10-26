import hmac
from functools import wraps

from flask import request

from src.errors import ForbiddenError


def require_admin_token(settings):
    """Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem ADMIN_TOKEN configurado, a rota fica bloqueada."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            token = request.headers.get("X-Admin-Token", "")
            if not settings.ADMIN_TOKEN or not hmac.compare_digest(token.encode(), settings.ADMIN_TOKEN.encode()):
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)
        return wrapper
    return decorator
