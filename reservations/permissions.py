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
        
        elif request.method == "POST" and view.action == "create":
            return is_student
        
        elif request.method == "PATCH" and view.action == "review":
            return is_labadmin or is_superuser

        elif request.method == "PATCH" and view.action == "cancel":
            return is_student
        
        return False

    def has_object_permission(self, request, view, obj):

        is_student = IsStudent().has_permission(request=request, view=view)
        is_superuser = IsSuperuser().has_permission(request=request, view=view)
        is_labadmin = IsLabAdmin().has_permission(request=request, view=view)

        if request.method in SAFE_METHODS:
            if is_superuser:
                return True

            if is_labadmin:
                labadmin = obj.reservationtime.lab.labadmin
                return (
                    labadmin is not None
                    and request.user.id == labadmin.user_id
                )

            if is_student:
                return request.user.id == obj.student.user_id

        if view.action == "review":
            return is_superuser or is_labadmin

        if view.action == "cancel":
            return is_student and request.user.id == obj.student.user_id

        return False
    
        