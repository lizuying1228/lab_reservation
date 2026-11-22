from reservations.models import Reservation
from reservation_times.models import ReservationTime
from labs.models import Laboratory
from rest_framework import serializers
from django.db import transaction
from datetime import datetime, time
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@transaction.atomic
def review_reservation(reservation_id, target_status):
    try:
        reservation_info = Reservation.objects.only("id", "reservationtime_id").get(id=reservation_id)
    except Reservation.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约记录不存在"})
    
    try:
        reservationtime = ReservationTime.objects.select_for_update().select_related("lab").get(
            id = reservation_info.reservationtime_id
        )
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约时段不存在"})

    try:
        reservation = Reservation.objects.select_for_update().get(id = reservation_id)
    except Reservation.DoesNotExist:
        raise serializers.ValidationError({"Error": "预约记录不存在"})

    if reservation.status != Reservation.StatusChoices.PENDING:
        raise serializers.ValidationError({"Error": "该预约不是待审核状态"})

    if reservationtime.is_deleted:
        raise serializers.ValidationError({"Error": "预约时段已停用"})

    lab = reservationtime.lab
    if lab.is_deleted or lab.status != Laboratory.StatusChoices.OPEN:
        raise serializers.ValidationError({"Error": "预约的实验室已停用或者未开放"})

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

    logger.info("Reservation reviewed successfully:"
                "reservation_id=%s, reservationtime_id=%s,"
                "target_status=%s", reservation.id, 
                reservationtime.id, target_status)

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
def cancel_reservation(reservation_id):
    try:
        reservation_info = Reservation.objects.only("id", "reservationtime_id").get(id = reservation_id)
    except Reservation.DoesNotExist:
        raise serializers.ValidationError({"Error": "此预约记录不存在"})

    try:
        reservationtime = ReservationTime.objects.select_for_update().get(
            id = reservation_info.reservationtime_id
        )
    except ReservationTime.DoesNotExist:
        raise serializers.ValidationError({"Error": "此预约时段不存在"})

    try:
        reservation = Reservation.objects.select_for_update().get(id = reservation_id)
    except Reservation.DoesNotExist:
        raise serializers.ValidationError({"Error": "此预约记录不存在"})

    prev_status = reservation.status

    if reservation.status == Reservation.StatusChoices.PENDING:
        pass

    elif reservation.status == Reservation.StatusChoices.APPROVED:
        if timezone.now() >= get_reservation_start_time(reservationtime=reservationtime):
            raise serializers.ValidationError({"Error": "预约时间一开始，不可取消"})

        exists = Reservation.objects.filter(
            status = Reservation.StatusChoices.APPROVED,
            reservationtime = reservationtime).exclude(id = reservation_id).exists()
        if exists:
            raise serializers.ValidationError({"Error": "存在其他预约通过该预约时间段"})

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

    logger.info("Reservation cancelled successfully: "
                "reservation_id=%s, reservationtime_id=%s," 
                "prev_status=%s", reservation.id, 
                reservationtime.id, prev_status)

    return reservation