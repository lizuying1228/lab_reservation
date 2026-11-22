
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.utils import timezone

from rest_framework import serializers

from labs.models import Laboratory
from lab_admins.models import LabAdmin
from reservation_times.models import ReservationTime
from reservations.models import Reservation

import logging


logger = logging.getLogger(__name__)
User = get_user_model()


def _validate_labadmin(labadmin, user):
    """验证实验室管理员及其关联账号是否可以被分配。"""

    if labadmin.is_deleted:
        raise serializers.ValidationError(
            {"Error": "不能分配给已删除的实验室管理员"}
        )

    if user.is_deleted or not user.is_active:
        raise serializers.ValidationError(
            {"Error": "不能分配给已禁用的实验室管理员"}
        )

    if user.is_superuser:
        raise serializers.ValidationError(
            {"Error": "不能将超级管理员分配为实验室管理员"}
        )


@transaction.atomic
def _create_laboratory_atomic(validated_data, operator_id):
    admin_no = validated_data.pop("labadmin_admin_no")

    # 先查询管理员 ID 和关联 User ID，不加锁。
    admin_info = (
        LabAdmin.objects
        .filter(admin_no=admin_no)
        .values("id", "user_id")
        .first()
    )

    if admin_info is None:
        raise serializers.ValidationError(
            {"Error": "实验室管理员不存在"}
        )

    # 第一步：锁定 User。
    try:
        user = User.objects.select_for_update().get(
            id=admin_info["user_id"]
        )
    except User.DoesNotExist:
        raise serializers.ValidationError(
            {"Error": "实验室管理员关联的用户不存在"}
        )

    # 第二步：锁定 LabAdmin。
    try:
        labadmin = LabAdmin.objects.select_for_update().get(
            id=admin_info["id"]
        )
    except LabAdmin.DoesNotExist:
        raise serializers.ValidationError(
            {"Error": "实验室管理员不存在"}
        )

    # 确认管理员与 User 的关联没有发生变化。
    if labadmin.user_id != user.id:
        raise serializers.ValidationError(
            {"Error": "管理员账号信息已变化，请重新提交"}
        )

    _validate_labadmin(labadmin, user)

    # 第三步：创建 Laboratory。
    lab = Laboratory.objects.create(
        labadmin=labadmin,
        **validated_data,
    )

    transaction.on_commit(
        lambda: logger.info(
            "Laboratory created successfully: "
            "lab_id=%s, lab_no=%s, labadmin_id=%s, operator_id=%s",
            lab.id,
            lab.lab_no,
            labadmin.id,
            operator_id,
        )
    )

    return lab


def create_laboratory(validated_data, operator_id):
    try:
        return _create_laboratory_atomic(
            validated_data=dict(validated_data),
            operator_id=operator_id,
        )

    except IntegrityError as exc:
        lab_no = validated_data["lab_no"]

        if Laboratory.objects.filter(lab_no=lab_no).exists():
            raise serializers.ValidationError(
                {"Error": "该实验室编号已存在"}
            ) from exc

        logger.exception(
            "Laboratory creation failed: operator_id=%s",
            operator_id,
        )

        raise serializers.ValidationError(
            {"Error": "创建实验室失败，请检查数据后重试"}
        ) from exc


@transaction.atomic
def update_laboratory(lab_id, validated_data, operator_id):

    # 先读取当前实验室的原管理员 ID。
    try:
        lab_info = Laboratory.objects.only(
            "labadmin_id"
        ).get(id=lab_id)

    except Laboratory.DoesNotExist:
        raise serializers.ValidationError(
            {"Error": "实验室不存在"}
        )

    target_labadmin = validated_data.get("labadmin")

    # 收集原管理员和目标管理员 ID。
    labadmin_ids = set()

    if lab_info.labadmin_id is not None:
        labadmin_ids.add(lab_info.labadmin_id)

    if target_labadmin is not None:
        labadmin_ids.add(target_labadmin.id)

    # 预先查询这些管理员关联的 User ID。
    # 此处不加锁，只用于确定接下来需要锁定哪些 User。
    admin_infos = list(
        LabAdmin.objects
        .filter(id__in=labadmin_ids)
        .values("id", "user_id")
    )

    admin_info_map = {
        info["id"]: info
        for info in admin_infos
    }

    user_ids = {
        info["user_id"]
        for info in admin_infos
    }

    # 第一步：按照 User ID 升序锁定所有关联 User。
    locked_users = list(
        User.objects.select_for_update()
        .filter(id__in=user_ids)
        .order_by("id")
    )

    user_map = {
        user.id: user
        for user in locked_users
    }

    # 第二步：按照 LabAdmin ID 升序锁定管理员。
    locked_labadmins = list(
        LabAdmin.objects.select_for_update()
        .filter(id__in=labadmin_ids)
        .order_by("id")
    )

    labadmin_map = {
        labadmin.id: labadmin
        for labadmin in locked_labadmins
    }

    # 检查原管理员是否存在。
    if (
        lab_info.labadmin_id is not None
        and lab_info.labadmin_id not in labadmin_map
    ):
        raise serializers.ValidationError(
            {"Error": "原实验室管理员不存在，请检查数据"}
        )

    # 检查目标管理员是否存在。
    if (
        target_labadmin is not None
        and target_labadmin.id not in labadmin_map
    ):
        raise serializers.ValidationError(
            {"Error": "目标实验室管理员不存在"}
        )

    # 检查管理员与 User 的关联是否发生变化。
    for admin_id, labadmin in labadmin_map.items():
        admin_info = admin_info_map[admin_id]

        if labadmin.user_id != admin_info["user_id"]:
            raise serializers.ValidationError(
                {"Error": "管理员账号信息已变化，请重新提交"}
            )

        if labadmin.user_id not in user_map:
            raise serializers.ValidationError(
                {"Error": "管理员关联的用户不存在"}
            )

    # 第三步：锁定 Laboratory。
    try:
        laboratory = Laboratory.objects.select_for_update().get(
            id=lab_id
        )

    except Laboratory.DoesNotExist:
        raise serializers.ValidationError(
            {"Error": "实验室不存在"}
        )

    if laboratory.is_deleted:
        raise serializers.ValidationError(
            {"Error": "该实验室已删除"}
        )

    # 检查读取原管理员 ID 后，是否被其他事务修改。
    if laboratory.labadmin_id != lab_info.labadmin_id:
        raise serializers.ValidationError(
            {"Error": "实验室管理员信息已变化，请重新提交"}
        )

    # 验证目标管理员。
    if target_labadmin is not None:
        locked_target = labadmin_map[target_labadmin.id]
        locked_user = user_map[locked_target.user_id]

        _validate_labadmin(locked_target, locked_user)

        # 使用锁定后的管理员对象。
        validated_data["labadmin"] = locked_target

    # 修改实验室状态前，检查是否存在任何预约历史。
    new_status = validated_data.get("status")

    if (
        new_status is not None
        and new_status != laboratory.status
        and Reservation.objects.filter(
            reservationtime__lab=laboratory
        ).exists()
    ):
        raise serializers.ValidationError(
            {"Error": "该实验室已有预约记录，不能修改实验室状态"}
        )

    # 只更新真正发生变化的字段。
    update_fields = []

    for field in ("position", "status", "labadmin"):

        if field not in validated_data:
            continue

        new_value = validated_data[field]

        if field == "labadmin":
            old_value = laboratory.labadmin_id
            new_value = (
                new_value.id
                if new_value is not None
                else None
            )
        else:
            old_value = getattr(laboratory, field)

        if old_value != new_value:
            setattr(
                laboratory,
                field,
                validated_data[field],
            )
            update_fields.append(field)

    if update_fields:
        laboratory.save(update_fields=update_fields)

        saved_fields = tuple(update_fields)

        transaction.on_commit(
            lambda: logger.info(
                "Laboratory updated successfully: "
                "lab_id=%s, lab_no=%s, update_fields=%s, operator_id=%s",
                laboratory.id,
                laboratory.lab_no,
                saved_fields,
                operator_id,
            )
        )

    return laboratory


@transaction.atomic
def delete_laboratory(lab_id, operator_id):

    # 第一步：锁定 Laboratory。
    try:
        laboratory = Laboratory.objects.select_for_update().get(
            id=lab_id
        )

    except Laboratory.DoesNotExist:
        raise serializers.ValidationError(
            {"Error": "实验室不存在"}
        )

    if laboratory.is_deleted:
        raise serializers.ValidationError(
            {"Error": "实验室已删除"}
        )

    # 第二步：锁定该实验室的所有预约时段。
    list(
        ReservationTime.objects.select_for_update()
        .filter(lab=laboratory)
        .order_by("id")
    )

    # 第三步：检查是否存在任何预约历史。
    exists = Reservation.objects.filter(
        reservationtime__lab=laboratory
    ).exists()

    if exists:
        logger.warning(
            "Laboratory deletion failed due to reservations: "
            "lab_id=%s, lab_no=%s, operator_id=%s",
            lab_id,
            laboratory.lab_no,
            operator_id,
        )

        raise serializers.ValidationError(
            {"Error": "该实验室有预约，禁止删除"}
        )

    # 第四步：软删除所有预约时段。
    now = timezone.now()

    deleted_count = ReservationTime.objects.filter(
        lab=laboratory,
        is_deleted=False,
    ).update(
        is_deleted=True,
        deleted_at=now,
    )

    # 第五步：软删除实验室。
    laboratory.is_deleted = True
    laboratory.deleted_at = now

    laboratory.save(
        update_fields=["is_deleted", "deleted_at"]
    )

    # 事务成功提交后再记录成功日志。
    transaction.on_commit(
        lambda: logger.info(
            "Laboratory deleted successfully: "
            "lab_id=%s, lab_no=%s, "
            "reservationtime_deleted_count=%s, operator_id=%s",
            laboratory.id,
            laboratory.lab_no,
            deleted_count,
            operator_id,
        )
    )

    return laboratory
      