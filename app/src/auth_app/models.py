import bcrypt
from django.db import models

NULLABLE = {"null": True, "blank": True}


class User(models.Model):
    """Модель пользователя."""

    email = models.EmailField(
        verbose_name="Email",
        help_text="Введите email",
        unique=True,
    )
    first_name = models.CharField(
        verbose_name="Имя",
        help_text="Введите имя",
        max_length=50,
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        help_text="Введите фамилию",
        max_length=50,
    )
    patronymic = models.CharField(
        verbose_name="Отчество",
        help_text="Введите отчество",
        max_length=50,
        **NULLABLE,
    )
    password_hash = models.CharField(
        verbose_name="Хэш пароля",
        help_text="Хранится только хэш пароля",
        max_length=255,
    )
    is_active = models.BooleanField(
        verbose_name="Активен",
        help_text="Активен ли пользователь",
        default=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата регистрации",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Последнее обновление",
    )

    class Meta:
        db_table = "users"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.email})"

    def set_password(self, raw_password):
        """Функция для установки пароля (хеширование)."""
        if not raw_password:
            raise ValueError("Ошибка: Пароль не может быть пустым.")
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(
            raw_password.encode("utf-8"),
            salt,
        ).decode("utf-8")

    def check_password(self, raw_password):
        """Функция для проверки пароля."""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(
            raw_password.encode("utf-8"),
            self.password_hash.encode("utf-8"),
        )

    def has_access(self, element_name, action, is_owner=True):
        """Проверка доступа к бизнес-объекту."""
        user_roles = UserRole.objects.filter(user=self).values_list(
            "role_id",
            flat=True,
        )
        try:
            rule = AccessRoleRule.objects.get(
                role_id__in=user_roles,
                element__name=element_name,
            )
        except AccessRoleRule.DoesNotExist:
            return False

        if action == "read":
            return rule.read_all or (rule.read and is_owner)
        elif action == "create":
            return rule.can_create
        elif action == "update":
            return rule.update_all or (rule.update and is_owner)
        elif action == "delete":
            return rule.delete_all or (rule.delete and is_owner)

        return False

    def get_permissions(self):
        """Возвращает список прав пользователя для всех бизнес-объектов."""
        user_roles = UserRole.objects.filter(user=self).values_list(
            "role_id",
            flat=True,
        )
        rules = AccessRoleRule.objects.filter(role_id__in=user_roles).select_related("element")

        permissions = []
        for rule in rules:
            permissions.append(
                {
                    "element": rule.element.name,
                    "read": rule.read,
                    "read_all": rule.read_all,
                    "create": rule.can_create,
                    "update": rule.update,
                    "update_all": rule.update_all,
                    "delete": rule.delete,
                    "delete_all": rule.delete_all,
                }
            )
        return permissions


class Role(models.Model):
    """Модель роли."""

    name = models.CharField(
        verbose_name="Название",
        help_text="Введите название",
        max_length=100,
        unique=True,
    )
    description = models.TextField(
        verbose_name="Описание",
        help_text="Введите описание",
        **NULLABLE,
    )

    class Meta:
        db_table = "roles"
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.name


class BusinessElement(models.Model):
    """Модель Бизнес-объекта."""

    name = models.CharField(
        verbose_name="Название бизнес-объекта",
        help_text="Например: users, reports, orders",
        max_length=100,
        unique=True,
    )
    description = models.TextField(
        verbose_name="Описание",
        help_text="Описание объекта",
        **NULLABLE,
    )

    class Meta:
        verbose_name = "Бизнес-объект"
        verbose_name_plural = "Бизнес-объекты"
        db_table = "business_elements"

    def __str__(self):
        return self.name


class AccessRoleRule(models.Model):
    """Модель правила доступа."""

    role = models.ForeignKey(
        Role,
        verbose_name="Роль",
        on_delete=models.CASCADE,
        related_name="access_rules",
    )
    element = models.ForeignKey(
        BusinessElement,
        verbose_name="Бизнес-объект",
        on_delete=models.CASCADE,
        related_name="access_rules",
    )
    read = models.BooleanField(
        default=False,
        verbose_name="Чтение своих",
    )
    read_all = models.BooleanField(
        default=False,
        verbose_name="Чтение всех",
    )
    can_create = models.BooleanField(
        default=False,
        verbose_name="Создание",
    )
    update = models.BooleanField(
        default=False,
        verbose_name="Обновление своих",
    )
    update_all = models.BooleanField(
        default=False,
        verbose_name="Обновление всех",
    )
    delete = models.BooleanField(
        default=False,
        verbose_name="Удаление своих",
    )
    delete_all = models.BooleanField(
        default=False,
        verbose_name="Удаление всех",
    )

    class Meta:
        verbose_name = "Правило доступа"
        verbose_name_plural = "Правила доступа"
        unique_together = ("role", "element")
        db_table = "access_role_rules"

    def __str__(self):
        return f"{self.role.name} → {self.element.name}"


class UserRole(models.Model):
    """Модель роли пользователя."""

    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        help_text="Выберите пользователя",
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        verbose_name="Роль",
        help_text="Выберите роль",
        on_delete=models.CASCADE,
        related_name="role_users",
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата назначения",
    )

    class Meta:
        db_table = "user_roles"
        verbose_name = "Роль пользователя"
        verbose_name_plural = "Роли пользователей"
        unique_together = ("user", "role")

    def __str__(self):
        return f"{self.user.email} -> {self.role.name}"
