from lab_admins.models import LabAdmin
from labs.models import Laboratory
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

@transaction.atomic
def delete_labadmin(labadmin_id, user_id):
    try:
        labadmin = LabAdmin.objects.select_for_update().get(id = labadmin_id)
    except LabAdmin.DoesNotExist:
        raise serializers.ValidationError({"Error": "该实验室管理员不存在"})

    if labadmin.is_deleted:
        raise serializers.ValidationError({"Error": "该实验室管理员已删除"})
    
    labs = list(Laboratory.objects.select_for_update().filter(labadmin=labadmin).order_by("id"))
    lab_count = Laboratory.objects.filter(labadmin=labadmin).update(labadmin=None)
    now = timezone.now()
    labadmin.is_deleted = True
    labadmin.deleted_at = now
    labadmin.save(update_fields=["is_deleted", "deleted_at"])

    logger.info("Labadmin deleted successfullly: "
                "labadmin_id=%s, lab_count=%s, user_id=%s",
                labadmin_id, lab_count, user_id)

    return labadmin