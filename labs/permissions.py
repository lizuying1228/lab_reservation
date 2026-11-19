from rest_framework.permissions import BasePermission, SAFE_METHODS
from users.permissions import IsLabAdmin, IsStudent, IsSuperuser

class LabPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        is_student = IsStudent().has_permission(request=request, view=view)
        is_labadmin = IsLabAdmin().has_permission(request=request, view=view)
        is_superuser = IsSuperuser().has_permission(request=request, view=view)

        if request.method in SAFE_METHODS:
            return is_student or is_labadmin or is_superuser

        elif request.method in ["POST", "DELETE", "PUT"]:
            return is_superuser

        elif request.method == "PATCH":
            return is_superuser or is_labadmin

        return False

    def has_object_permission(self, request, view, obj):

        is_student = IsStudent().has_permission(request=request, view=view)
        is_labadmin = IsLabAdmin().has_permission(request=request, view=view)
        is_superuser = IsSuperuser().has_permission(request=request, view=view)

        if is_student:
            return request.method in SAFE_METHODS

        elif is_superuser:
            return True

        elif is_labadmin:
            if obj.labadmin:
                return request.user.id == obj.labadmin.user_id and (
                    request.method in SAFE_METHODS or request.method == "PATCH")

        return False
        