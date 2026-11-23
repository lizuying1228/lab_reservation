from labs.models import Laboratory
from labs.permissions import LabPermission
from labs.serializers import LaboratoryCreateSerializer, LaboratorySerializer
from labs.services import delete_laboratory
from rest_framework.viewsets import ModelViewSet
from rest_framework import serializers
import logging

logger = logging.getLogger(__name__)
# Create your views here.
class LabViewSet(ModelViewSet):
    permission_classes = [LabPermission]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or hasattr(user, "student"):
            return Laboratory.objects.filter(is_deleted=False).select_related("labadmin")
        elif hasattr(user, "labadmin"):
            return Laboratory.objects.filter(is_deleted=False, labadmin__user=user).select_related("labadmin")
        return Laboratory.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return LaboratoryCreateSerializer
        return LaboratorySerializer

    def perform_update(self, serializer):
        user = self.request.user
        if hasattr(user, "labadmin") and "labadmin" in serializer.validated_data:
            raise serializers.ValidationError({"Error": "实验室管理员不允许修改管理员"})
        serializer.save()

    def perform_destroy(self, instance):
        operator_id = self.request.user.id
        delete_laboratory(lab_id=instance.id, operator_id=operator_id)
        