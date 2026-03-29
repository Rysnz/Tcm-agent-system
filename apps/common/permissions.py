from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffUser(BasePermission):
    """仅允许后台管理用户访问"""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)


class IsStaffOrReadOnly(BasePermission):
    """读开放，写仅后台管理用户"""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)
