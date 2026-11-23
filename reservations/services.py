from reservations.models import Reservation
from reservation_times.models import ReservationTime
from students.models import Student
from labs.models import Laboratory
from rest_framework import serializers
from django.db import transaction, IntegrityError
from datetime import datetime, time
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@transaction.atomic
def review_reservation(reservation_id, target_status, operator_id):
    try:
        reservation_info = Reservation.objects.only("id", "reservationtime_id").get(id=reservation_id)
    except Reservation.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约记录不存在"})

    try:
        reservationtime_info = ReservationTime.objects.only("lab_id").get(id = reservation_info.reservationtime_id)
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "该预约时段不存在"})

    try:
        laboratory = Laboratory.objects.select_for_update().get(id = reservationtime_info.lab_id)
    except Laboratory.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约时段实验室不存在"})

    if laboratory.is_deleted or laboratory.status != Laboratory.StatusChoices.OPEN:
        raise serializers.ValidationError({"Error": "预约时段实验室已删除或者已停用"})
    
    try:
        reservationtime = ReservationTime.objects.select_for_update().select_related("lab").get(
            id = reservation_info.reservationtime_id
        )
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约时段不存在"})

    if reservationtime.lab_id != laboratory.id:
        raise serializers.ValidationError({"Error": "预约时段实验室变化，请重试"})

    if reservationtime.is_deleted:
        raise serializers.ValidationError({"Error": "预约时段已停用"})

    try:
        reservation = Reservation.objects.select_for_update().get(id = reservation_id)
    except Reservation.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约记录不存在"})

    if reservation.status != Reservation.StatusChoices.PENDING:
        raise serializers.ValidationError({"Error": "该预约不是待审核状态"})

    if target_status == Reservation.StatusChoices.APPROVED:
        if reservationtime.status != ReservationTime.StatusChoices.AVAILABLE:
            raise serializers.ValidationError({"Error": "预约时段已被占用"})

        exists = Reservation.objects.filter(
            reservationtime=reservationtime,
            status=Reservation.StatusChoices.APPROVED
        ).exclude(id = reservation.id).exists()
        if exists:
            raise serializers.ValidationError({"Error": "预约时段已存在其他通过的预约"})

        reservationtime.status = ReservationTime.StatusChoices.OCCUPIED
        reservationtime.save(update_fields=["status"])

    elif target_status == Reservation.StatusChoices.REJECTED:
        pass
    else:
        raise serializers.ValidationError({"Error": "该审核状态不支持"})

    reservation.status = target_status
    reservation.save(update_fields=["status"])

    transaction.on_commit(lambda: logger.info("Reservation reviewed successfully:"
                "reservation_id=%s, reservationtime_id=%s,"
                "target_status=%s, operator_id=%s", reservation.id, 
                reservationtime.id, target_status, operator_id))

    return reservation
        

TIME_STARTS = {
    "morning": time(8, 0),
    "afternoon": time(14, 0),
    "evening": time(19, 0)
}

def get_reservation_start_time(reservationtime):
    start_time = TIME_STARTS.get(reservationtime.time)
    if start_time is None:
        raise serializers.ValidationError({"Error": "不支持的预约时段"})
    
    start_datetime = datetime.combine(
        reservationtime.date, 
        start_time
    )
    return timezone.make_aware(start_datetime, timezone.get_current_timezone())

@transaction.atomic
def cancel_reservation(reservation_id, operator_id):
    try:
        reservation_info = Reservation.objects.only("id", "reservationtime_id").get(id = reservation_id)
    except Reservation.DoesNotExist:
        raise serializers.ValidationError({"Error": "此预约记录不存在"})

    try:
        reservationtime_info = ReservationTime.objects.only("lab_id").get(id = reservation_info.reservationtime_id)
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "该预约时段不存在"})

    try:
        laboratory = Laboratory.objects.select_for_update().get(id = reservationtime_info.lab_id)
    except Laboratory.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约时段实验室不存在"})

    if laboratory.is_deleted or laboratory.status != Laboratory.StatusChoices.OPEN:
        raise serializers.ValidationError({"Error": "预约时段实验室已删除或者已停用"})

    try:
        reservationtime = ReservationTime.objects.select_for_update().get(
            id = reservation_info.reservationtime_id
        )
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "此预约时段不存在"})

    if reservationtime.lab_id != laboratory.id:
        raise serializers.ValidationError({"Error": "预约时段实验室变化，请重试"})

    if reservationtime.is_deleted:
        raise serializers.ValidationError({"Error": "预约时段已删除"})

    try:
        reservation = Reservation.objects.select_for_update().get(id = reservation_id)
    except Reservation.DoesNotExist:
        raise serializers.ValidationError({"Error": "此预约记录不存在"})

    prev_status = reservation.status

    if reservation.status == Reservation.StatusChoices.PENDING:
        pass

    elif reservation.status == Reservation.StatusChoices.APPROVED:
        if timezone.now() >= get_reservation_start_time(reservationtime=reservationtime):
            raise serializers.ValidationError({"Error": "预约时间已开始，不可取消"})

        exists = Reservation.objects.filter(
            status = Reservation.StatusChoices.APPROVED,
            reservationtime = reservationtime).exclude(id = reservation_id).exists()
        if not exists:
            reservationtime.status = ReservationTime.StatusChoices.AVAILABLE
            reservationtime.save(update_fields=["status"])

    elif reservation.status == Reservation.StatusChoices.REJECTED:
        raise serializers.ValidationError({"Error": "预约已拒绝，不可取消"})

    elif reservation.status == Reservation.StatusChoices.CANCELLED:
        raise serializers.ValidationError({"Error": "不可重复取消"})

    else:
        raise serializers.ValidationError({"Error": "预约状态异常"})

    reservation.status = Reservation.StatusChoices.CANCELLED
    reservation.save(update_fields=["status"])

    transaction.on_commit(lambda:logger.info("Reservation cancelled successfully: "
                "reservation_id=%s, reservationtime_id=%s," 
                "prev_status=%s, operator_id=%s", reservation.id, 
                reservationtime.id, prev_status, operator_id))

    return reservation


def _validated_student(student, user):
    if student.is_deleted:
        raise serializers.ValidationError({"Error": "该学生已删除"})
    
    if user.is_deleted:
        raise serializers.ValidationError({"Error": "该学生关联用户已删除"})

    if not user.is_active:
        raise serializers.ValidationError({"Error": "该学生关联用户已禁用"})

    
@transaction.atomic
def _create_reservation_atomic(validated_data, operator_id):
    reservationtime_id = validated_data.get("reservationtime_id")
    try:
        user = User.objects.select_for_update().get(id = operator_id)
    except User.DoesNotExist:
        raise serializers.ValidationError({"Error": "该学生关联用户不存在"})

    try:
        student = Student.objects.select_for_update().get(user_id = user.id)
    except Student.DoesNotExist:
        raise serializers.ValidationError({"Error": "该学生不存在"})

    _validated_student(student, user)

    try:
        reservationtime_info = ReservationTime.objects.only("lab_id").get(id = reservationtime_id)
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约时段不存在"})

    try:
        laboratory = Laboratory.objects.select_for_update().get(id = reservationtime_info.lab_id)
    except Laboratory.DoesNotExist:
        raise serializers.ValidationError({"Error": "实验室不存在"})

    if laboratory.is_deleted or laboratory.status != Laboratory.StatusChoices.OPEN:
        raise serializers.ValidationError({"Error": "实验室已删除或者已停用"})

    try:
        reservationtime = ReservationTime.objects.select_for_update().get(id = reservationtime_id)
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约时段不存在"})

    if laboratory.id != reservationtime.lab_id:
        raise serializers.ValidationError({"Error": "预约时段实验室变化，请重试"})

    today = timezone.localdate()

    if reservationtime.date <= today:
        raise serializers.ValidationError({"Error": "预约日期必须从明天开始"})

    if reservationtime.date > today + timedelta(days=7):
        raise serializers.ValidationError({"Error": "只能预约未来七天的时间"})

    if reservationtime.status != ReservationTime.StatusChoices.AVAILABLE:
        raise serializers.ValidationError({"Error": "预约时间已被占用"})

    reservation = Reservation.objects.create(student=student, reservationtime=reservationtime)
    transaction.on_commit(lambda: logger.info("Reservation created successfully: "
                                              "reservation_id=%s, reservationtime_id=%s,"
                                              "student_id=%s, operator_id=%s",
                                              reservation.id, reservation.reservationtime_id,
                                              student.id, operator_id))
    return reservation


def create_reservation(validated_data, operator_id):
    try:
        return _create_reservation_atomic(validated_data=validated_data, operator_id=operator_id)
    except IntegrityError:
        student = Student.objects.get(user_id = operator_id)
        reservationtime = ReservationTime.objects.get(id = validated_data.get("reservationtime_id"))
        if Reservation.objects.filter(student=student, reservationtime=reservationtime).exists():
            raise serializers.ValidationError({"Error": "您已预约过该时段，不可重复预约"})
        raise serializers.ValidationError({"Error": "数据库数据异常变化，请重试"})



    