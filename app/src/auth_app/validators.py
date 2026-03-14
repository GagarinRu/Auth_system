import re

from django.core.exceptions import ValidationError


def validate_password_strength(value):
    """
    Универсальный валидатор сложности пароля.
    Может использоваться в сериализаторах, формах, админке.
    """
    if len(value) < 8:
        raise ValidationError("Пароль должен содержать не менее 8 символов.")
    if not re.search(r"[a-z]", value):
        raise ValidationError("Пароль должен содержать хотя бы одну строчную букву.")
    if not re.search(r"[A-Z]", value):
        raise ValidationError("Пароль должен содержать хотя бы одну заглавную букву.")
    if not re.search(r"\d", value):
        raise ValidationError("Пароль должен содержать хотя бы одну цифру.")
    if not re.search(r"[@$!%*#?&]", value):
        raise ValidationError("Пароль должен содержать хотя бы один спецсимвол: @$!%*#?&")


def validate_unique_email(value):
    """Проверяет уникальность email."""
    from .models import User

    if User.objects.filter(email=value).exists():
        raise ValidationError("Пользователь с таким email уже существует.")
