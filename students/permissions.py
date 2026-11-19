from rest_framework.permissions import BasePermission, SAFE_METHODS
from users.permissions import IsLabAdmin, IsStudent, IsSuperuser

class StudentPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        is_student = IsStudent().has_permission(request=request, view=view)
        is_superuser = IsSuperuser().has_permission(request=request, view=view)
        is_labadmin = IsLabAdmin().has_permission(request=request, view=view)

        if request.method in SAFE_METHODS:
            return is_student or is_superuser or is_labadmin
        
        elif request.method in ["POST", "PUT", "DELETE"]:
            return is_superuser
        
        elif request.method == "PATCH":
            return is_student or is_superuser

        return False

    def has_object_permission(self, request, view, obj):

        is_student = IsStudent().has_permission(request=request, view=view)
        is_superuser = IsSuperuser().has_permission(request=request, view=view)
        is_labadmin = IsLabAdmin().has_permission(request=request, view=view)

        if is_superuser:
            return True

        elif is_student:
            return (obj.user_id == request.user.id) and (
                request.method in SAFE_METHODS or request.method == "PATCH")

        elif is_labadmin:
            return request.method in SAFE_METHODS

        return False
        


