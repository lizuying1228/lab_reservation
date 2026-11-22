from labs.models import Laboratory
from reservation_times.models import ReservationTime
from reservations.models import Reservation
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@transaction.atomic
def delete_laboratory(lab_id, user_id):
    try:
        laboratory = Laboratory.objects.select_for_update().get(id = lab_id)
    except Laboratory.DoesNotExist:
        raise serializers.ValidationError({"Error": "实验室不存在"})

    if laboratory.is_deleted:
        raise serializers.ValidationError({"Error": "实验室已删除"})

    reservationtimes = list(ReservationTime.objects.select_for_update().filter(lab=laboratory).order_by("id"))

    exists = Reservation.objects.filter(reservationtime__lab=laboratory).exists()
    if exists:
        logger.warning("Laboratory deletion failed due to reservations: "
                       "lab_id=%s, lab_no=%s, user_id=%s", lab_id, laboratory.lab_no, user_id)
        raise serializers.ValidationError({"Error": "该实验室有预约，禁止删除"})

    now = timezone.now()
    deleted_count = ReservationTime.objects.select_for_update().filter(
        lab=laboratory, 
        is_deleted=False
        ).update(is_deleted=True, deleted_at=now)
    laboratory.is_deleted = True
    laboratory.deleted_at = now
    laboratory.save(update_fields=["is_deleted", "deleted_at"])

    logger.info("Laboratory deleted successfully:"
                "lab_id=%s, lab_no=%s, reservationtime_deleted_count=%s, user_id=%s", 
                laboratory.id, laboratory.lab_no, deleted_count, user_id)

    return laboratory
            