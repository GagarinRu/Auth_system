from django.core.validators import EmailValidator
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField, EmailField, IntegerField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer, Serializer

from .models import AccessRoleRule, BusinessElement, Role, User, UserRole
from .validators import validate_password_strength, validate_unique_email


class RegisterSerializer(Serializer):
    """Сериализатор для регистрации."""

    email = EmailField(
        validators=[
            EmailValidator(message="Некорректный email"),
            validate_unique_email,
        ],
        help_text="Email пользователя",
    )
    first_name = CharField(
        max_length=50,
        help_text="Имя",
    )
    last_name = CharField(
        max_length=50,
        help_text="Фамилия",
    )
    patronymic = CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="Отчество",
    )
    password = CharField(
        write_only=True,
        validators=[validate_password_strength],
        help_text="Пароль (минимум 8 символов, 1 заглавная, 1 строчная, цифра, спецсимвол)",
    )
    password_confirm = CharField(
        write_only=True,
        help_text="Подтверждение пароля",
    )

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise ValidationError({"password_confirm": "Пароли не совпадают."})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        raw_password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(raw_password)
        user.save()

        return user


class LoginSerializer(Serializer):
    """Сериализатор для авторизации."""

    email = EmailField(
        help_text="Email",
    )
    password = CharField(
        write_only=True,
        help_text="Пароль",
    )

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            raise ValidationError({"email": "Неверный email или пользователь не активен."}) from None
        if not user.check_password(password):
            raise ValidationError({"password": "Неверный пароль."})
        data["user"] = user
        return data


class ProfileSerializer(ModelSerializer):
    """Сериализатор для профиля пользователя."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "patronymic", "email"]
        read_only_fields = ["email"]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr != "email":
                setattr(instance, attr, value)
        instance.save()
        return instance


class UserDeleteSerializer(Serializer):
    """Сериализатор для "мягкого" удаления — просто деактивация."""

    confirm = BooleanField(
        help_text="Подтвердите удаление (true)",
        write_only=True,
    )

    def validate_confirm(self, value):
        if not value:
            raise ValidationError("Для удаления аккаунта необходимо подтвердить действие.")
        return value

    def save(self):
        user = self.context["request"].user
        user.is_active = False
        user.save()
        return user


class BusinessElementSerializer(ModelSerializer):
    """Сериализатор для бизнес-объектов."""

    class Meta:
        model = BusinessElement
        fields = ["id", "name", "description"]


class AccessRuleSerializer(ModelSerializer):
    """Сериализатор для правил доступа."""

    element_name = CharField(source="element.name", read_only=True)

    class Meta:
        model = AccessRoleRule
        fields = [
            "element_name",
            "read",
            "read_all",
            "create",
            "update",
            "update_all",
            "delete",
            "delete_all",
        ]


class RoleSerializer(ModelSerializer):
    """Сериализатор для ролей."""

    access_rules = AccessRuleSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ["id", "name", "description", "access_rules"]


class RoleCreateUpdateSerializer(Serializer):
    """Сериализатор для создания/обновления роли с правами доступа."""

    name = CharField(max_length=100, help_text="Название роли")
    description = CharField(required=False, allow_blank=True, help_text="Описание")
    element_ids = PrimaryKeyRelatedField(
        queryset=BusinessElement.objects.all(),
        many=True,
        write_only=True,
        help_text="Список ID бизнес-объектов",
    )
    read = BooleanField(default=False)
    read_all = BooleanField(default=False)
    create_perm = BooleanField(default=False)
    update_perm = BooleanField(default=False)
    update_all = BooleanField(default=False)
    delete = BooleanField(default=False)
    delete_all = BooleanField(default=False)

    def create(self, validated_data):
        element_ids = validated_data.pop("element_ids", [])
        flags = {
            "read": validated_data.pop("read", False),
            "read_all": validated_data.pop("read_all", False),
            "create": validated_data.pop("create_perm", False),
            "update": validated_data.pop("update_perm", False),
            "update_all": validated_data.pop("update_all", False),
            "delete": validated_data.pop("delete", False),
            "delete_all": validated_data.pop("delete_all", False),
        }

        role = Role.objects.create(**validated_data)
        for elem_id in element_ids:
            AccessRoleRule.objects.create(role=role, element_id=elem_id, **flags)
        return role

    def update(self, instance, validated_data):
        element_ids = validated_data.pop("element_ids", None)
        flags = {
            "read": validated_data.pop("read", False),
            "read_all": validated_data.pop("read_all", False),
            "create": validated_data.pop("create_perm", False),
            "update": validated_data.pop("update_perm", False),
            "update_all": validated_data.pop("update_all", False),
            "delete": validated_data.pop("delete", False),
            "delete_all": validated_data.pop("delete_all", False),
        }

        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.save()

        if element_ids is not None:
            AccessRoleRule.objects.filter(role=instance).delete()
            for elem_id in element_ids:
                AccessRoleRule.objects.create(role=instance, element_id=elem_id, **flags)

        return instance


class UserRoleAssignSerializer(Serializer):
    """Сериализатор для присвоения роли пользователю."""

    user_id = IntegerField(help_text="ID пользователя")
    role_id = IntegerField(help_text="ID роли")

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            if not user.is_active:
                raise ValidationError("Пользователь не активен.")
            return user
        except User.DoesNotExist:
            raise ValidationError("Пользователь не найден.") from None

    def validate_role_id(self, value):
        try:
            return Role.objects.get(id=value)
        except Role.DoesNotExist:
            raise ValidationError("Роль не найдена.") from None

    def save(self):
        user = self.validated_data["user_id"]
        role = self.validated_data["role_id"]
        user_role, created = UserRole.objects.update_or_create(user=user, role=role, defaults={})
        return user_role


class UserRoleRemoveSerializer(Serializer):
    """Сериализатор для удаления роли пользователю."""

    user_id = IntegerField(help_text="ID пользователя")
    role_id = IntegerField(help_text="ID роли")

    def validate_user_id(self, value):
        try:
            return User.objects.get(id=value)
        except User.DoesNotExist:
            raise ValidationError("Пользователь не найден.") from None

    def validate_role_id(self, value):
        try:
            return Role.objects.get(id=value)
        except Role.DoesNotExist:
            raise ValidationError("Роль не найдена.") from None

    def save(self):
        user = self.validated_data["user_id"]
        role = self.validated_data["role_id"]
        try:
            UserRole.objects.get(user=user, role=role).delete()
        except UserRole.DoesNotExist:
            pass
        return {"message": f"Роль {role.name} удалена у пользователя {user.email}"}
