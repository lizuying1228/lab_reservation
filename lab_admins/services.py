from lab_admins.models import LabAdmin
from labs.models import Laboratory
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@transaction.atomic
def delete_labadmin(labadmin_id, operator_id):
    try:
        labadmin_info = LabAdmin.objects.only("user_id").get(id = labadmin_id)
    except LabAdmin.DoesNotExist:
        raise serializers.ValidationError({"Error": "该实验室管理员不存在"})

    try:
        user = User.objects.select_for_update().get(id = labadmin_info.user_id)
    except User.DoesNotExist:
        raise serializers.ValidationError({"Error": "该用户不存在"})

    try:
        labadmin = LabAdmin.objects.select_for_update().get(id = labadmin_id)
    except LabAdmin.DoesNotExist:
        raise serializers.ValidationError({"Error": "该实验室管理员不存在"})

    if labadmin.user_id != user.id:
        raise serializers.ValidationError({"Error": "管理员关联用户变化，请重试"})

    if labadmin.is_deleted:
        raise serializers.ValidationError({"Error": "该实验室管理员已删除"})
    
    labs = list(Laboratory.objects.select_for_update().filter(labadmin=labadmin).order_by("id"))
    lab_count = len(labs)
    Laboratory.objects.filter(labadmin=labadmin).update(labadmin=None)

    now = timezone.now()
    user.is_active = False
    user.save(update_fields=["is_active"])

    labadmin.is_deleted = True
    labadmin.deleted_at = now
    labadmin.save(update_fields=["is_deleted", "deleted_at"])

    transaction.on_commit(lambda: logger.info("Labadmin deleted successfullly: "
                "labadmin_id=%s, lab_count=%s, operator_id=%s",
                labadmin_id, lab_count, operator_id))

    return labadmin


@transaction.atomic
def _create_labadmin_atomic(validated_data, operator_id):
    username = validated_data.get("username")
    password = validated_data.get("password")
    name = validated_data.get("name")
    admin_no = validated_data.get("admin_no")
    birth_date = validated_data.get("birth_date")

    user = User.objects.create_user(username=username, password=password)
    labadmin = LabAdmin.objects.create(user=user, name=name, admin_no=admin_no, birth_date=birth_date)

    transaction.on_commit(lambda: logger.info("LabAdmin created successfully: "
                "labadmin_id=%s, admin_no=%s, operator_id=%s",
                labadmin.id, labadmin.admin_no, operator_id))

    return labadmin

def create_labadmin(validated_data, operator_id):
    try:
        return _create_labadmin_atomic(validated_data=validated_data, operator_id=operator_id)
    except IntegrityError:
        admin_no = validated_data.get("admin_no")
        username = validated_data.get("username")
        if LabAdmin.objects.filter(admin_no = admin_no).exists():
            raise serializers.ValidationError({"Error": "实验室管理员编号重复"})

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"Error": "用户名重复"})

        logger.exception("LabAdmin created failed due to Integrity error: "
                    "operator_id=%s", operator_id)

        raise serializers.ValidationError({"Error": "创建管理员失败，数据库异常变化"})


@transaction.atomic
def update_labadmin(labadmin_id, validated_data, operator_id):
    try:
        labadmin = LabAdmin.objects.select_for_update().get(id = labadmin_id)
    except LabAdmin.DoesNotExist:
        raise serializers.ValidationError({"Error": "该管理员不存在"})

    if labadmin.is_deleted:
        raise serializers.ValidationError({"Error": "该管理员已删除"})

    name = validated_data.get("name")
    birth_date = validated_data.get("birth_date")

    update_fields = []
    if name is not None and labadmin.name != name:
        labadmin.name = name
        update_fields.append("name")

    if birth_date is not None and labadmin.birth_date != birth_date:
        labadmin.birth_date = birth_date
        update_fields.append("birth_date")

    if update_fields:
        labadmin.save(update_fields=update_fields)
        transaction.on_commit(lambda: logger.info("LabAdmin updated successfully: "
                    "labadmin_id=%s, admin_no=%s, update_fields=%s, operator_id=%s",
                    labadmin.id, labadmin.admin_no, update_fields, operator_id))

    return labadmin

        