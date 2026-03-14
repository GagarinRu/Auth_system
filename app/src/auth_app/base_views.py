from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class AuthenticatedAPIView(APIView):
    """Базовый класс для view, требующих аутентификации."""

    def check_authentication(self, request):
        """Проверяет, аутентифицирован ли пользователь."""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Не аутентифицирован"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return None

    def check_access(self, request, element_name, action, is_owner=True):
        """Проверяет доступ к элементу."""
        if not request.user.has_access(element_name, action, is_owner=is_owner):
            return Response(
                {"error": "Доступ запрещён"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None
