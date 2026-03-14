from django.core.management.base import BaseCommand

from auth_app.models import AccessRoleRule, BusinessElement, Role


class Command(BaseCommand):
    help = "Инициализация RBAC (создание ролей и правил доступа)"

    def handle(self, *args, **options):
        self.stdout.write("Creating roles...")
        roles_data = [
            ("admin", "Administrator"),
            ("user", "Regular user"),
            ("manager", "Manager"),
        ]
        for name, desc in roles_data:
            Role.objects.get_or_create(name=name, defaults={"description": desc})
        self.stdout.write(self.style.SUCCESS("Роли созданы"))
        self.stdout.write("Создание бизнес-объектов ...")
        elements_data = [
            ("documents", "Documents"),
            ("orders", "Orders"),
            ("products", "Products"),
            ("roles", "Role management"),
        ]
        for name, desc in elements_data:
            BusinessElement.objects.get_or_create(name=name, defaults={"description": desc})
        self.stdout.write(self.style.SUCCESS("Бизнес-объекты созданы"))
        admin_role = Role.objects.get(name="admin")
        for element in BusinessElement.objects.all():
            AccessRoleRule.objects.get_or_create(
                role=admin_role,
                element=element,
                defaults={
                    "read": True,
                    "read_all": True,
                    "can_create": True,
                    "update": True,
                    "update_all": True,
                    "delete": True,
                    "delete_all": True,
                },
            )
        self.stdout.write(self.style.SUCCESS("Права доступа Admin созданы."))
        user_role = Role.objects.get(name="user")
        user_elements = ["products", "documents", "orders"]
        for elem_name in user_elements:
            element = BusinessElement.objects.get(name=elem_name)
            AccessRoleRule.objects.get_or_create(
                role=user_role,
                element=element,
                defaults={
                    "read": True,
                    "read_all": False,
                    "can_create": False,
                    "update": False,
                    "update_all": False,
                    "delete": False,
                    "delete_all": False,
                },
            )
        self.stdout.write(self.style.SUCCESS("Права доступа User созданы."))
        manager_role = Role.objects.get(name="manager")
        orders = BusinessElement.objects.get(name="orders")
        AccessRoleRule.objects.get_or_create(
            role=manager_role,
            element=orders,
            defaults={
                "read": True,
                "read_all": True,
                "can_create": True,
                "update": True,
                "update_all": True,
                "delete": True,
                "delete_all": True,
            },
        )
        products = BusinessElement.objects.get(name="products")
        AccessRoleRule.objects.get_or_create(
            role=manager_role,
            element=products,
            defaults={
                "read": True,
                "read_all": False,
                "can_create": False,
                "update": False,
                "update_all": False,
                "delete": False,
                "delete_all": False,
            },
        )
        self.stdout.write(self.style.SUCCESS("Права доступа Manager созданы."))
        self.stdout.write(self.style.SUCCESS("RBAC инициализирован!"))
