from datetime import timedelta
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from students.models import Student
from labs.models import Laboratory
from reservation_times.models import ReservationTime
from reservations.models import Reservation

User = get_user_model()

with transaction.atomic():
    suffix = uuid4().hex[:8]

    # 1. 创建测试用户和学生
    user = User.objects.create_user(
        username=f"delete_test_{suffix}",
        password="Test123456",
    )

    student = Student.objects.create(
        user=user,
        name="软删除测试学生",
        student_no=f"DEL{suffix.upper()}",
        birth_date="2005-01-01",
    )

    # 2. 找一个有效且开放的实验室
    lab = Laboratory.objects.filter(
        is_deleted=False,
        status=Laboratory.StatusChoices.OPEN,
    ).first()

    if lab is None:
        raise Exception("没有可用的开放实验室")

    # 3. 创建四个预约时段
    dates = [
        timezone.localdate() + timedelta(days=10),
        timezone.localdate() + timedelta(days=11),
    ]

    slots = []

    for date in dates:
        for period in ["morning", "afternoon"]:
            slot = ReservationTime.objects.create(
                lab=lab,
                date=date,
                time=period,
                status=ReservationTime.StatusChoices.AVAILABLE,
            )
            slots.append(slot)

    # 4. 创建四种预约状态
    statuses = [
        Reservation.StatusChoices.PENDING,
        Reservation.StatusChoices.APPROVED,
        Reservation.StatusChoices.REJECTED,
        Reservation.StatusChoices.CANCELLED,
    ]

    reservations = []

    for slot, status_value in zip(slots, statuses):
        reservation = Reservation.objects.create(
            student=student,
            reservationtime=slot,
            status=status_value,
        )
        reservations.append(reservation)

        if status_value == Reservation.StatusChoices.APPROVED:
            slot.status = ReservationTime.StatusChoices.OCCUPIED
            slot.save(update_fields=["status"])

    print("测试学生 ID:", student.id)
    print("测试用户名:", user.username)
    print("测试实验室:", lab.lab_no)

    for reservation in reservations:
        print(
            f"预约 ID={reservation.id}, "
            f"时段 ID={reservation.reservationtime_id}, "
            f"状态={reservation.status}"
        )