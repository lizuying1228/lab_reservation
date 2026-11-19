from rest_framework.permissions import BasePermission

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if hasattr(user, "student"):
            student = user.student
            return (user.is_authenticated and not user.is_superuser and not hasattr(user, "labadmin") 
                    and not user.is_deleted and not student.is_deleted and user.is_active)
        return False

class IsLabAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if hasattr(user, "labadmin"):
            labadmin = user.labadmin
        return (user.is_authenticated and not user.is_superuser and not hasattr(user, "student")
                and not user.is_deleted and not labadmin.is_deleted and user.is_active)

class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return (user.is_authenticated and user.is_superuser and not hasattr(user, "student") 
                and not hasattr(user, "labadmin") and not user.is_deleted)
