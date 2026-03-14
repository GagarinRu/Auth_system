from django.urls import path

from .views import (
    BusinessElementListView,
    LoginView,
    LogoutView,
    MockDocumentDetailView,
    MockDocumentListView,
    MockOrderListView,
    MockProductListView,
    ProfileView,
    RegisterView,
    RoleCreateView,
    RoleListView,
    RoleUpdateView,
    UserDeleteView,
    UserRoleAssignView,
    UserRoleRemoveView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("delete-account/", UserDeleteView.as_view(), name="delete-account"),
    path("business-element/", BusinessElementListView.as_view(), name="business-element-list"),
    path("roles/", RoleListView.as_view(), name="role-list"),
    path("roles/create/", RoleCreateView.as_view(), name="role-create"),
    path("roles/<int:role_id>/update/", RoleUpdateView.as_view(), name="role-update"),
    path("user-role/assign/", UserRoleAssignView.as_view(), name="user-role-assign"),
    path("user-role/remove/", UserRoleRemoveView.as_view(), name="user-role-remove"),
    path("documents/", MockDocumentListView.as_view(), name="document-list"),
    path("documents/<int:doc_id>/", MockDocumentDetailView.as_view(), name="document-detail"),
    path("orders/", MockOrderListView.as_view(), name="order-list"),
    path("products/", MockProductListView.as_view(), name="product-list"),
]
