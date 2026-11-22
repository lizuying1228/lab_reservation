from lab_admins.models import LabAdmin
from lab_admins.serializers import LabAdminCreateSerializer, LabAdminSerializer
from lab_admins.permissions import LabAdminPermission
from rest_framework.viewsets import ModelViewSet
from lab_admins.services import delete_labadmin
import logging

logger = logging.getLogger(__name__)
# Create your views here.

class LabAdminViewSet(ModelViewSet):
    permission_classes = [LabAdminPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return LabAdmin.objects.filter(is_deleted=False).select_related("user")
        
        elif hasattr(user, "labadmin"):
            return LabAdmin.objects.filter(user=user, is_deleted=False).select_related("user")

        return LabAdmin.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return LabAdminCreateSerializer
        return LabAdminSerializer

    def perform_destroy(self, instance):
        operator_id = self.request.user.id
        delete_labadmin(labadmin_id=instance.id, operator_id=operator_id)
        

        