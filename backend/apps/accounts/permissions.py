from rest_framework.permissions import BasePermission


def role_permission(*roles):
    """
    Crea un permiso que solo deja pasar a usuarios autenticados con alguno de los roles.

    Uso en una vista:
        permission_classes = [role_permission(User.Role.PSICOLOGO)]
    """

    class RolePermission(BasePermission):
        message = "No tienes permisos para realizar esta acción."

        def has_permission(self, request, view):
            user = request.user
            return bool(user and user.is_authenticated and user.role in roles)

    return RolePermission
