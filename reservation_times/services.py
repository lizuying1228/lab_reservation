from reservation_times.models import ReservationTime
from labs.models import Laboratory
from reservations.models import Reservation
from rest_framework import serializers
from django.db import transaction, IntegrityError
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@transaction.atomic
def delete_reservationtime(reservationtime_id, operator_id):
    try:
        reservationtime_info = ReservationTime.objects.only("lab_id").get(id = reservationtime_id)
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约时段不存在"})

    try:
        laboratory = Laboratory.objects.select_for_update().get(id = reservationtime_info.lab_id)
    except Laboratory.DoesNotExist:
        raise serializers.ValidationError({"Error": "实验室不存在"})

    if laboratory.is_deleted:
        raise serializers.ValidationError({"Error": "实验室已删除"})
    
    try:
        reservationtime = ReservationTime.objects.select_for_update().get(id = reservationtime_id)
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约时段不存在"})

    if reservationtime.lab_id != laboratory.id:
        raise serializers.ValidationError({"Error": "预约时段实验室错误，请重试"})

    if reservationtime.is_deleted:
        raise serializers.ValidationError({"Error": "预约时段已删除"})

    exists = Reservation.objects.filter(reservationtime=reservationtime).exists()
    if exists:
        raise serializers.ValidationError({"Error": "该时段有预约记录，不可删除"})

    reservationtime.is_deleted = True
    reservationtime.deleted_at = timezone.now()
    reservationtime.save(update_fields=["is_deleted", "deleted_at"])

    transaction.on_commit(lambda: logger.info("ReservationTime deleted successfully:"
                "reservationtime_id=%s, lab_id=%s, user_id=%s",
                reservationtime.id, reservationtime.lab_id, operator_id))

    return reservationtime


@transaction.atomic
def update_reservationtime(reservationtime_id, validated_data, operator_id):
    try:
        reservationtime_info = ReservationTime.objects.only("lab_id").get(id = reservationtime_id)
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约时段不存在"})

    original_lab_id = reservationtime_info.lab_id
    target_lab = validated_data.get("lab")
    target_lab_id = target_lab.id if target_lab else original_lab_id

    lab_ids = sorted(set([original_lab_id, target_lab_id]))

    labs = Laboratory.objects.select_for_update().filter(id__in = lab_ids).order_by("id")

    lab_map = {lab.id: lab for lab in labs}

    if len(lab_map) != len(lab_ids):
        raise serializers.ValidationError({"Error": "实验室不存在"})

    try:
        reservationtime = ReservationTime.objects.select_for_update().get(id = reservationtime_id)
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约时段不存在"})

    if reservationtime.is_deleted:
        raise serializers.ValidationError({"Error": "预约时段已删除"})

    if reservationtime.lab_id != original_lab_id:
        raise serializers.ValidationError({"Error": "预约原实验室异常变化"})

    original_lab = lab_map[original_lab_id]
    new_lab = lab_map[target_lab_id]

    if original_lab.is_deleted:
        raise serializers.ValidationError({"Error": "原实验室已删除"})

    if new_lab.is_deleted:
        raise serializers.ValidationError({"Error": "不能选择已删除的实验室"})

    if new_lab.status != Laboratory.StatusChoices.OPEN:
        raise serializers.ValidationError({"Error": "只能选择开放的实验室"})
    
    if Reservation.objects.filter(reservationtime=reservationtime).exists():
        logger.warning("ReservationTime updated failed: user_id=%s, reservationtime_id=%s", operator_id, reservationtime_id)
        raise serializers.ValidationError({"Error": "该预约时段有预约记录，不可修改"})

    new_date = validated_data.get("date", reservationtime.date)
    new_time = validated_data.get("time", reservationtime.time)
    if new_date != reservationtime.date:
        if new_date <= timezone.localdate():
            raise serializers.ValidationError({"Error": "修改日期必须从明天开始"})

    exists = ReservationTime.objects.filter(
        lab=new_lab,
        date=new_date,
        time=new_time
    ).exclude(id=reservationtime.id).exists()

    if exists:
        raise serializers.ValidationError({
            "Error": "该实验室已经存在相同日期和时间的预约时段"
        })
    
    for field, value in validated_data.items():
        setattr(reservationtime, field, value)

    if validated_data:
        reservationtime.save(update_fields=list(validated_data.keys()))

    transaction.on_commit(lambda: logger.info("ReservationTime updated successfully: " \
            "reservationtime_id=%s, original_lab_id=%s, target_lab_id=%s, user_id=%s",
            reservationtime.id, original_lab_id, target_lab_id, operator_id))

    return reservationtime

@transaction.atomic
def _create_reservationtime_atomic(validated_data, operator_id, labadmin_id=None, is_superuser=False):
    # 1. 取得请求中的实验室编号
    lab_no = validated_data["lab_no"]

    # 2. 锁定实验室
    try:
        lab = Laboratory.objects.select_for_update().get(
            lab_no=lab_no
        )
    except Laboratory.DoesNotExist:
        logger.warning(
            "ReservationTime created failed: "
            "lab not found, lab_no=%s, operator_id=%s",
            lab_no, operator_id
        )
        raise serializers.ValidationError({
            "Error": "该实验室不存在"
        })

    # 3. 检查实验室是否已经软删除
    if lab.is_deleted:
        raise serializers.ValidationError({
            "Error": "该实验室已删除"
        })

    # 4. 检查实验室是否开放
    if lab.status != Laboratory.StatusChoices.OPEN:
        raise serializers.ValidationError({
            "Error": "只能为开放状态的实验室创建预约时段"
        })

    # 5. 检查管理员是否有权管理该实验室
    if not is_superuser and (labadmin_id is None or lab.labadmin_id != labadmin_id):
        logger.warning(
            "ReservationTime created failed: "
            "permission denied, lab_id=%s, operator_id=%s, is_superuser=%s",
            lab.id, operator_id, is_superuser
        )
        raise serializers.ValidationError({
            "Error": "不允许创建其他管理员的实验室时段"
        })

    # 6. 在事务中重新检查预约日期
    date = validated_data["date"]
    if date <= timezone.localdate():
        raise serializers.ValidationError({
            "Error": "预约时间必须从明天开始"
        })

    # # 7. 检查是否已经存在相同的预约时段
    # exists = ReservationTime.objects.filter(
    #     lab=lab,
    #     date=date,
    #     time=validated_data["time"]
    # ).exists()

    # if exists:
    #     raise serializers.ValidationError({
    #         "Error": "该实验室的时间段已添加，不可重复添加"
    #     })

    # 8. 创建预约时段
    reservationtime = ReservationTime.objects.create(
        lab=lab,
        date=date,
        time=validated_data["time"]
    )

    # 9. 记录成功日志
    transaction.on_commit(lambda: logger.info(
        "ReservationTime created successfully: "
        "reservationtime_id=%s, lab_id=%s, lab_no=%s, operator_id=%s",
        reservationtime.id,
        lab.id,
        lab.lab_no,
        operator_id
    ))

    return reservationtime

def create_reservationtime(validated_data, operator_id, labadmin_id=None, is_superuser=False):
    try:
        return _create_reservationtime_atomic(
            validated_data=validated_data, 
            operator_id=operator_id,
            labadmin_id=labadmin_id, 
            is_superuser=is_superuser
            )
    except IntegrityError:
        lab_no = validated_data.get("lab_no")
        lab = Laboratory.objects.get(lab_no=lab_no)
        if ReservationTime.objects.filter(
            lab=lab, 
            date=validated_data.get("date"),
            time=validated_data.get("time")
            ).exists():
            raise serializers.ValidationError({"Error": "该实验室预约时段重复，请重选时段"})
        raise serializers.ValidationError({"Error": "数据库数据异常"})

    

    

    


    

    