from django.db import transaction, IntegrityError
from students.models import Student
from lab_admins.models import LabAdmin
from rest_framework import serializers
from reservations.models import Reservation
from reservation_times.models import ReservationTime
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@transaction.atomic
def delete_student(student_id, operator_id):
    try:
        student_info = Student.objects.only("user_id").get(id = student_id)
    except Student.DoesNotExist:
        raise serializers.ValidationError({"Error": "该学生不存在"})

    try:
        user = User.objects.select_for_update().get(id = student_info.user_id)
    except User.DoesNotExist:
        raise serializers.ValidationError({"Error": "该用户不存在"})
    
    try:
        student = Student.objects.select_for_update().get(id = student_id)
    except Student.DoesNotExist:
        raise serializers.ValidationError({"Error": "该学生不存在"})

    if student.user_id != user.id:
        raise serializers.ValidationError({"Error": "学生关联用户发生变化，请重试"})

    if student.is_deleted:
        raise serializers.ValidationError({"Error": "该学生已删除"})

    active_statuses = [Reservation.StatusChoices.APPROVED, Reservation.StatusChoices.PENDING]
    reservationtime_ids = list(Reservation.objects.filter(student = student, status__in = active_statuses)
                               .values_list("reservationtime_id", flat=True).distinct())

    cancelled_count = 0
    if reservationtime_ids:
        reservationtimes = list(ReservationTime.objects.select_for_update()
                                .filter(id__in = reservationtime_ids).order_by("id"))
        reservationtime_map = {
            item.id: item for item in reservationtimes
        }

        reservations = list(Reservation.objects.select_for_update()
                            .filter(student = student, status__in = active_statuses).order_by("id"))

        approved_time_ids = set()

        for reservation in reservations:
            prev_status = reservation.status

            if prev_status == Reservation.StatusChoices.APPROVED:
                approved_time_ids.add(reservation.reservationtime_id)

            reservation.status = Reservation.StatusChoices.CANCELLED
            reservation.save(update_fields=["status"])
            cancelled_count += 1

            logger.info("Reservation cancelled successfully due to student deleted: "
                        "reservation_id=%s, student_id=%s, reservationtime_id=%s, "
                        "previous_status=%s, operator_id=%s", reservation.id, student.id,
                        reservation.reservationtime_id, prev_status, operator_id)

        for reservationtime_id in approved_time_ids:
            reservationtime = reservationtime_map.get(reservationtime_id)
            if reservationtime is None:
                raise serializers.ValidationError({"Error": "预约时段不存在"})

            exists = Reservation.objects.filter(
                reservationtime = reservationtime,
                status = Reservation.StatusChoices.APPROVED
            ).exists()
            if not exists and not reservationtime.is_deleted:
                reservationtime.status = ReservationTime.StatusChoices.AVAILABLE
                reservationtime.save(update_fields=["status"])

                logger.info("ReservationTime available successfully due to student deleted:"
                            "reservationtime_id=%s, student_id=%s, previous_status=%s, operator_id=%s",
                            reservationtime_id, student.id, ReservationTime.StatusChoices.OCCUPIED, operator_id)

    student.is_deleted = True
    student.deleted_at = timezone.now()
    student.save(update_fields=["is_deleted", "deleted_at"])

    user.is_active = False
    user.save(update_fields=["is_active"])

    logger.info("Student deleted successfully:" \
                "student_id=%s, reservation_cancelled_count=%s, operator_id=%s", 
                student.id, cancelled_count, operator_id)

    return student


@transaction.atomic
def _create_student_atomic(validated_data, operator_id):
    name = validated_data.get("name")
    student_no = validated_data.get("student_no")
    birth_date = validated_data.get("birth_date")
    user_id = validated_data.get("user_id")
    username = validated_data.get("username")
    password = validated_data.get("password")

    if user_id is not None:
        try:
            user = User.objects.select_for_update().get(id = user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({"Error": "该用户不存在"})

        if user.is_deleted or not user.is_active:
            raise serializers.ValidationError({"Error": "该用户已停用或已删除"})

        if user.is_superuser:
            raise serializers.ValidationError({"Error": "该用户已绑定超级管理员身份"})

        if LabAdmin.objects.filter(user_id = user.id).exists():
            raise serializers.ValidationError({"Error": "该用户已绑定实验室管理员"})

        if Student.objects.filter(user_id = user.id).exists():
            raise serializers.ValidationError({"Error": "该用户已绑定学生档案"})
    else:
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"Error": "该用户名重复，请重试"})
        user = User.objects.create_user(username=username, password=password)

    student = Student.objects.create(name=name, student_no=student_no, birth_date=birth_date, user=user)

    logger.info("Student created successfully: "
                "student_id=%s, student_no=%s, user_id=%s, operator_id=%s",
                student.id, student.student_no, user.id, operator_id)

    return student

def create_student(validated_data, operator_id):
    try:
        return _create_student_atomic(validated_data=validated_data, operator_id=operator_id)
    except IntegrityError:
        student_no = validated_data.get("student_no")
        username = validated_data.get("username")
        user_id = validated_data.get("user_id")

        if student_no and Student.objects.filter(student_no=student_no).exists():
            raise serializers.ValidationError({"Error": "该学号已存在"})

        if user_id is not None:
            if Student.objects.filter(user_id=user_id).exists():
                raise serializers.ValidationError({"Error": "该用户已绑定学生"})

            if LabAdmin.objects.filter(user_id=user_id).exists():
                raise serializers.ValidationError({"Error": "该用户已绑定实验室管理员"})

        if username and User.objects.filter(username=username):
            raise serializers.ValidationError({"Error": "该用户已存在"})

        logger.exception(
            "Student creation failed due to database integrity error: "
            "operator_id=%s",
            operator_id,
        )

        raise serializers.ValidationError({"Error": "创建学生失败，数据库发生变化，请重试"})

@transaction.atomic
def update_student(student_id, validated_data, operator_id):
    try:
        student = Student.objects.select_for_update().get(id = student_id)
    except Student.DoesNotExist:
        raise serializers.ValidationError({"Error": "学生不存在"})

    if student.is_deleted:
        raise serializers.ValidationError({"Error": "学生已删除"})

    name = validated_data.get("name")
    birth_date = validated_data.get("birth_date")

    update_fields = []
    if name and student.name != name:
        student.name = name
        update_fields.append("name")

    if birth_date and student.birth_date != birth_date:
        student.birth_date = birth_date
        update_fields.append("birth_date")

    if update_fields:
        student.save(update_fields=update_fields)
        logger.info("Student updated successfully: "
                    "student_id=%s, update_fields=%s, operator=%s",
                    student.id, update_fields, operator_id)

    return student
    