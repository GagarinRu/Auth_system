import jwt as pyjwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from .models import User


class AuthenticatedAnonymousUser(AnonymousUser):
    """Расширенный AnonymousUser с методом has_access."""

    @property
    def is_authenticated(self):
        return False

    def has_access(self, element_name, action, is_owner=True):
        return False

    def get_permissions(self):
        return []


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware для аутентификации по JWT.
    Устанавливает request.user, если токен валиден.
    """

    def process_request(self, request):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            request.user = AuthenticatedAnonymousUser()
            request._user = request.user
            return
        token = auth_header.split(" ")[1]
        try:
            payload = pyjwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user = User.objects.get(id=payload["user_id"], is_active=True)
            user.is_authenticated = True
            user.is_active = True
            request.user = user
            request._user = user
        except (ExpiredSignatureError, InvalidTokenError, User.DoesNotExist):
            request.user = AuthenticatedAnonymousUser()
            request._user = request.user
