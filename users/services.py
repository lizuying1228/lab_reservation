from students.services import delete_student
from lab_admins.services import delete_labadmin
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (OutstandingToken, BlacklistedToken,)
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@transaction.atomic
def delete_user(target_user_id, operator_id):
    try:
        user = User.objects.select_for_update().get(id=target_user_id)
    except User.DoesNotExist:
        raise serializers.ValidationError({"Error": "该用户不存在"})

    if user.is_deleted:
        raise serializers.ValidationError({"Error": "该用户已删除"})

    if user.is_superuser:
        raise serializers.ValidationError({"Error": "超级管理员禁止删除"})

    auth_type = "normal"
    if hasattr(user, "student"):
        auth_type = "student"
        student = user.student
        if not student.is_deleted:
            delete_student(student_id=student.id, user_id=operator_id)

    elif hasattr(user, "labadmin"):
        auth_type = "labadmin"
        labadmin = user.labadmin
        if not labadmin.is_deleted:
            delete_labadmin(labadmin_id=labadmin.id, user_id=operator_id)


    outstanding_tokens = OutstandingToken.objects.filter(user=user)
    for token in outstanding_tokens:
        BlacklistedToken.objects.get_or_create(token = token)

    user.is_deleted = True
    user.is_active = False
    user.deleted_at = timezone.now()
    user.save(update_fields=["is_deleted", "is_active", "deleted_at"])

    logger.info("User deleted successfully: "
                "deleted_user_id=%s, auth_type=%s, operater_id=%s",
                target_user_id, auth_type, operator_id)

    return user