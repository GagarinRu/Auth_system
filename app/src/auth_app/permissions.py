from functools import wraps

from rest_framework import status
from rest_framework.response import Response

from auth_app.models import UserRole


def require_access(element_name, action):
    """Декоратор для проверки доступа к бизнес-объекту."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            if not hasattr(request, "user") or not request.user.is_authenticated:
                return Response(
                    {"error": "Не аутентифицирован"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if not request.user.has_access(element_name, action, is_owner=True):
                return Response(
                    {"error": "Доступ запрещён"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return view_func(self, request, *args, **kwargs)

        return wrapper

    return decorator


def require_role(role_name):
    """Декоратор для проверки роли (альтернатива, если хочешь по ролям)."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            if not hasattr(request, "user") or not request.user.is_authenticated:
                return Response(
                    {"error": "Не аутентифицирован"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            has_role = UserRole.objects.filter(user=request.user, role__name=role_name).exists()
            if not has_role:
                return Response({"error": "Доступ запрещён"}, status=status.HTTP_403_FORBIDDEN)
            return view_func(self, request, *args, **kwargs)

        return wrapper

    return decorator
