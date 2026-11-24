from reservation_times.models import ReservationTime
from reservation_times.serializers import ReservationTimeCreateSerializer, ReservationTimeSerializer
from reservation_times.permissions import ReservationTimePermission
from reservation_times.services import delete_reservationtime, update_reservationtime, create_reservationtime
from rest_framework.viewsets import ModelViewSet
from rest_framework import serializers
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
# Create your views here.
class ReservationTimeViewSet(ModelViewSet):
    permission_classes = [ReservationTimePermission]
    filterset_fields = ["lab", "date", "time", "status"]
    search_fields = ["lab__lab_no", "lab__position"]
    ordering_fields = ["id", "date", "time", "status"]
    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or hasattr(user, "student"):
            return ReservationTime.objects.filter(is_deleted=False, lab__is_deleted=False, date__gte=timezone.localdate()).select_related("lab")
        
        elif hasattr(user, "labadmin"):
            return ReservationTime.objects.filter(is_deleted=False, lab__is_deleted=False, lab__labadmin__user=user,  date__gte=timezone.localdate()).select_related("lab")

        return ReservationTime.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ReservationTimeCreateSerializer
        return ReservationTimeSerializer

    def perform_create(self, serializer):
        user = self.request.user
        labadmin_id = None

        if hasattr(user, "labadmin"):
            labadmin_id = user.labadmin.id
        
        reservationtime = create_reservationtime(
            validated_data=serializer.validated_data,
            operator_id=user.id,
            labadmin_id=labadmin_id,
            is_superuser=user.is_superuser
        )

        serializer.instance = reservationtime


    def perform_update(self, serializer):
        user = self.request.user
  
        if hasattr(user, "labadmin") and ("lab" in serializer.validated_data):
            logger.warning("ReservationTime updated failed: user_id=%s", user.id)
            raise serializers.ValidationError({"Error": "实验室不可以修改"})
        
        reservationtime = update_reservationtime(
            reservationtime_id=serializer.instance.id,             
            validated_data=serializer.validated_data,
            operator_id=user.id)
        
        serializer.instance = reservationtime


    def perform_destroy(self, instance):
        user = self.request.user
        delete_reservationtime(reservationtime_id=instance.id, operator_id=user.id)


        
        