from rest_framework.permissions import BasePermission, SAFE_METHODS
from users.permissions import IsLabAdmin, IsStudent, IsSuperuser

class ReservationPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        is_student = IsStudent().has_permission(request=request, view=view)
        is_superuser = IsSuperuser().has_permission(request=request, view=view)
        is_labadmin = IsLabAdmin().has_permission(request=request, view=view)
        
        if request.method in SAFE_METHODS:
            return is_student or is_labadmin or is_superuser
        
        elif request.method == "POST":
            return is_student
        
        elif request.method in ["PUT", "PATCH"]:
            return is_labadmin or is_superuser
        
        return False

    def has_object_permission(self, request, view, obj):

        is_student = IsStudent().has_permission(request=request, view=view)
        is_superuser = IsSuperuser().has_permission(request=request, view=view)
        is_labadmin = IsLabAdmin().has_permission(request=request, view=view)

        if is_superuser:
            return request.method in SAFE_METHODS or request.method in ["PUT", "PATCH"]
        
        elif is_labadmin:
            labadmin = obj.reservationtime.lab.labadmin
            if labadmin is not None and request.user.id == labadmin.user_id:
                return request.method in SAFE_METHODS or request.method in ["PUT", "PATCH"]

        elif is_student:
            if request.user.id == obj.student.user_id:
                return request.method in SAFE_METHODS
            
        return False
    
        