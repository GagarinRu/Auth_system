import logging
from datetime import datetime, timedelta

import jwt as pyjwt
from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .base_views import AuthenticatedAPIView
from .mock_data import MOCK_DOCUMENTS, MOCK_ORDERS, MOCK_PRODUCTS
from .models import AccessRoleRule, BusinessElement, Role, UserRole
from .permissions import require_access
from .serializers import (
    BusinessElementSerializer,
    LoginSerializer,
    ProfileSerializer,
    RegisterSerializer,
    RoleCreateUpdateSerializer,
    RoleSerializer,
    UserDeleteSerializer,
    UserRoleAssignSerializer,
    UserRoleRemoveSerializer,
)

logger = logging.getLogger(__name__)


def generate_jwt(user):
    """Генерация JWT токена вручную."""
    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS),
        "iat": datetime.utcnow(),
    }
    token = pyjwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


class RegisterView(APIView):
    """Регистрация нового пользователя."""

    @extend_schema(
        summary="Регистрация",
        description="Создание нового пользователя",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description="Пользователь успешно создан"),
            400: OpenApiResponse(description="Ошибка валидации"),
        },
        tags=["Auth"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            try:
                default_role = Role.objects.get(name="user")
                UserRole.objects.get_or_create(user=user, role=default_role)
            except Role.DoesNotExist:
                logger.warning("Роль 'user' не найдена. Пользователь создан без роли.")
            return Response(
                {
                    "message": "Пользователь успешно зарегистрирован.",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Логин пользователя и выдача JWT."""

    @extend_schema(
        summary="Вход",
        description="Аутентификация и получение JWT токена",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Успешный вход, токен получен"),
            400: OpenApiResponse(description="Неверные учетные данные"),
        },
        tags=["Auth"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            token = generate_jwt(user)
            return Response(
                {
                    "message": "Успешный вход",
                    "access_token": token,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "permissions": user.get_permissions(),
                    },
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Логаут — в stateless JWT просто возвращаем успех, клиент сам удалит токен."""

    @extend_schema(
        summary="Выход",
        description="Выход из системы (удаление токена на клиенте)",
        responses={200: OpenApiResponse(description="Успешный выход")},
        tags=["Auth"],
    )
    def post(self, request):
        return Response({"message": "Вы успешно вышли из системы."}, status=status.HTTP_200_OK)


class ProfileView(AuthenticatedAPIView):
    """Просмотр и обновление профиля."""

    @extend_schema(
        summary="Профиль",
        description="Получение данных текущего пользователя",
        responses={200: OpenApiResponse(description="Данные профиля")},
        tags=["Profile"],
    )
    def get(self, request):
        auth_error = self.check_authentication(request)
        if auth_error:
            return auth_error
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Обновление профиля",
        description="Обновление данных профиля",
        request=ProfileSerializer,
        responses={200: OpenApiResponse(description="Профиль обновлён")},
        tags=["Profile"],
    )
    def put(self, request):
        auth_error = self.check_authentication(request)
        if auth_error:
            return auth_error
        serializer = ProfileSerializer(request.user, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDeleteView(AuthenticatedAPIView):
    """Мягкое удаление аккаунта."""

    @extend_schema(
        summary="Удаление аккаунта",
        description="Мягкое удаление (деактивация) аккаунта пользователя",
        request=UserDeleteSerializer,
        responses={200: OpenApiResponse(description="Аккаунт деактивирован")},
        tags=["Profile"],
    )
    def delete(self, request):
        auth_error = self.check_authentication(request)
        if auth_error:
            return auth_error
        serializer = UserDeleteSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Аккаунт успешно деактивирован."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleListView(APIView):
    """Список всех ролей с правами."""

    @extend_schema(
        summary="Список ролей",
        description="Получение всех ролей с правами доступа",
        responses={200: OpenApiResponse(description="Список ролей")},
        tags=["Roles"],
    )
    @require_access("roles", "read")
    def get(self, request):
        roles = Role.objects.prefetch_related("access_rules__element")
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)


class RoleCreateView(APIView):
    """Создание новой роли."""

    @extend_schema(
        summary="Создание роли",
        description="Создание новой роли с правами доступа",
        request=RoleCreateUpdateSerializer,
        responses={201: OpenApiResponse(description="Роль создана")},
        tags=["Roles"],
    )
    @require_access("roles", "create")
    def post(self, request):
        serializer = RoleCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleUpdateView(APIView):
    """Обновление роли."""

    @extend_schema(
        summary="Обновление роли",
        description="Обновление роли и её прав доступа",
        request=RoleCreateUpdateSerializer,
        responses={200: OpenApiResponse(description="Роль обновлена")},
        tags=["Roles"],
    )
    @require_access("roles", "update")
    def put(self, request, role_id):
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({"error": "Роль не найдена."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RoleCreateUpdateSerializer(role, data=request.data, partial=False)
        if serializer.is_valid():
            role = serializer.save()
            return Response(RoleSerializer(role).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRoleAssignView(APIView):
    """Назначение роли пользователю."""

    @extend_schema(
        summary="Назначение роли",
        description="Назначение роли пользователю",
        request=UserRoleAssignSerializer,
        responses={200: OpenApiResponse(description="Роль назначена")},
        tags=["Roles"],
    )
    @require_access("roles", "read")
    def post(self, request):
        serializer = UserRoleAssignSerializer(data=request.data)
        if serializer.is_valid():
            user_role = serializer.save()
            return Response(
                {"message": f"Роль {user_role.role.name} назначена пользователю {user_role.user.email}"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserRoleRemoveView(APIView):
    """Удаление роли у пользователя."""

    @extend_schema(
        summary="Удаление роли",
        description="Удаление роли у пользователя",
        request=UserRoleRemoveSerializer,
        responses={200: OpenApiResponse(description="Роль удалена")},
        tags=["Roles"],
    )
    @require_access("roles", "read")
    def post(self, request):
        serializer = UserRoleRemoveSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BusinessElementListView(APIView):
    """Список бизнес-объектов."""

    @extend_schema(
        summary="Бизнес-объекты",
        description="Список бизнес-объектов системы",
        responses={200: OpenApiResponse(description="Список объектов")},
        tags=["Roles"],
    )
    @require_access("roles", "read")
    def get(self, request):
        elements = BusinessElement.objects.all()
        serializer = BusinessElementSerializer(elements, many=True)
        return Response(serializer.data)


class MockDocumentListView(AuthenticatedAPIView):
    """Список документов."""

    @extend_schema(
        summary="Список документов",
        description="Получение списка документов (mock)",
        responses={200: OpenApiResponse(description="Список документов")},
        tags=["Business Objects"],
        operation_id="documents_list",
    )
    def get(self, request):
        auth_error = self.check_authentication(request)
        if auth_error:
            return auth_error
        access_error = self.check_access(request, "documents", "read", is_owner=True)
        if access_error:
            return access_error
        user_roles = UserRole.objects.filter(user=request.user).values_list("role_id", flat=True)
        try:
            rule = AccessRoleRule.objects.get(
                role_id__in=user_roles,
                element__name="documents",
            )
            if rule.read_all:
                return Response(MOCK_DOCUMENTS)
        except AccessRoleRule.DoesNotExist:
            pass
        return Response([d for d in MOCK_DOCUMENTS if d["owner_id"] == request.user.id])

    @extend_schema(
        summary="Создание документа",
        description="Создание нового документа (mock)",
        responses={201: OpenApiResponse(description="Документ создан")},
        tags=["Business Objects"],
        operation_id="documents_create",
    )
    def post(self, request):
        auth_error = self.check_authentication(request)
        if auth_error:
            return auth_error
        access_error = self.check_access(request, "documents", "create", is_owner=False)
        if access_error:
            return access_error
        return Response(
            {"message": "Документ создан (mock)", "owner_id": request.user.id},
            status=status.HTTP_201_CREATED,
        )


class MockDocumentDetailView(AuthenticatedAPIView):
    """Детали документа."""

    @extend_schema(
        summary="Документ",
        description="Получение документа по ID (mock)",
        responses={200: OpenApiResponse(description="Документ")},
        tags=["Business Objects"],
        operation_id="document_detail",
    )
    def get(self, request, doc_id):
        auth_error = self.check_authentication(request)
        if auth_error:
            return auth_error
        doc = next((d for d in MOCK_DOCUMENTS if d["id"] == doc_id), None)
        if not doc:
            return Response({"error": "Документ не найден"}, status=status.HTTP_404_NOT_FOUND)
        is_owner = doc["owner_id"] == request.user.id
        access_error = self.check_access(request, "documents", "read", is_owner=is_owner)
        if access_error:
            return access_error
        return Response(doc)

    @extend_schema(
        summary="Обновление документа",
        description="Обновление документа по ID (mock)",
        responses={200: OpenApiResponse(description="Документ обновлён")},
        tags=["Business Objects"],
        operation_id="document_update",
    )
    def put(self, request, doc_id):
        auth_error = self.check_authentication(request)
        if auth_error:
            return auth_error
        doc = next((d for d in MOCK_DOCUMENTS if d["id"] == doc_id), None)
        if not doc:
            return Response({"error": "Документ не найден"}, status=status.HTTP_404_NOT_FOUND)
        is_owner = doc["owner_id"] == request.user.id
        access_error = self.check_access(request, "documents", "update", is_owner=is_owner)
        if access_error:
            return access_error
        return Response({"message": "Документ обновлен (mock)", "id": doc_id})

    @extend_schema(
        summary="Удаление документа",
        description="Удаление документа по ID (mock)",
        responses={200: OpenApiResponse(description="Документ удалён")},
        tags=["Business Objects"],
        operation_id="document_delete",
    )
    def delete(self, request, doc_id):
        auth_error = self.check_authentication(request)
        if auth_error:
            return auth_error
        doc = next((d for d in MOCK_DOCUMENTS if d["id"] == doc_id), None)
        if not doc:
            return Response({"error": "Документ не найден"}, status=status.HTTP_404_NOT_FOUND)
        is_owner = doc["owner_id"] == request.user.id
        access_error = self.check_access(request, "documents", "delete", is_owner=is_owner)
        if access_error:
            return access_error
        return Response({"message": "Документ удален (mock)", "id": doc_id})


class MockOrderListView(AuthenticatedAPIView):
    """Список заказов."""

    @extend_schema(
        summary="Список заказов",
        description="Получение списка заказов (mock)",
        responses={200: OpenApiResponse(description="Список заказов")},
        tags=["Business Objects"],
        operation_id="orders_list",
    )
    def get(self, request):
        auth_error = self.check_authentication(request)
        if auth_error:
            return auth_error
        access_error = self.check_access(request, "orders", "read", is_owner=True)
        if access_error:
            return access_error
        user_roles = UserRole.objects.filter(user=request.user).values_list("role_id", flat=True)
        try:
            rule = AccessRoleRule.objects.get(
                role_id__in=user_roles,
                element__name="orders",
            )
            if rule.read_all:
                return Response(MOCK_ORDERS)
        except AccessRoleRule.DoesNotExist:
            pass
        return Response([o for o in MOCK_ORDERS if o["owner_id"] == request.user.id])


class MockProductListView(AuthenticatedAPIView):
    """Список товаров."""

    @extend_schema(
        summary="Список товаров",
        description="Получение списка товаров (mock)",
        responses={200: OpenApiResponse(description="Список товаров")},
        tags=["Business Objects"],
        operation_id="products_list",
    )
    def get(self, request):
        auth_error = self.check_authentication(request)
        if auth_error:
            return auth_error
        access_error = self.check_access(request, "products", "read", is_owner=True)
        if access_error:
            return access_error
        return Response(MOCK_PRODUCTS)
