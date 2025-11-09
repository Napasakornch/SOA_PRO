from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_admin())

class IsSellerUser(permissions.BasePermission):
    """
    Allows access only to seller users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_seller())

class IsSellerOrAdminUser(permissions.BasePermission):
    """
    Allows access to seller and admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_seller() or request.user.is_admin()))