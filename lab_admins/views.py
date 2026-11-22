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

    def perform_create(self, serializer):
        labadmin = serializer.save()
        logger.info("LabAdmin created successfully: labadmin_id=%s, user_id=%s", labadmin.id, labadmin.user_id)

    def perform_destroy(self, instance):
        user = self.request.user
        delete_labadmin(labadmin_id=instance.id, user_id=user.id)
        

        