from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db import transaction

from students.models import Student
from lab_admins.models import LabAdmin
from labs.models import Laboratory
from reservation_times.models import ReservationTime
from reservations.models import Reservation

User = get_user_model()

with transaction.atomic():
    # 1. 创建学生账号和档案
    student_user = User.objects.create_user(
        username="delete_test_student",
        password="Test123456",
    )

    student = Student.objects.create(
        user=student_user,
        name="删除测试学生",
        student_no="DELETE_TEST_001",
        birth_date=date(2005, 1, 1),
    )

    # 2. 创建管理员账号和档案
    admin_user = User.objects.create_user(
        username="delete_test_admin",
        password="Test123456",
    )

    lab_admin = LabAdmin.objects.create(
        user=admin_user,
        name="删除测试管理员",
        admin_no="DELETE_ADMIN_001",
        birth_date=date(1990, 1, 1),
    )

    # 3. 创建管理员负责的实验室
    lab = Laboratory.objects.create(
        lab_no="DELETE_TEST_LAB",
        position="删除测试实验室",
        labadmin=lab_admin,
        status="OPEN",
    )

    # 4. 创建两个未来预约时段
    tomorrow = date.today() + timedelta(days=1)

    morning = ReservationTime.objects.create(
        lab=lab,
        date=tomorrow,
        time="morning",
        status="occupied",
    )

    afternoon = ReservationTime.objects.create(
        lab=lab,
        date=tomorrow,
        time="afternoon",
        status="available",
    )

    # 5. 创建学生预约记录
    Reservation.objects.create(
        student=student,
        reservationtime=morning,
        status="approved",
    )

    Reservation.objects.create(
        student=student,
        reservationtime=afternoon,
        status="pending",
    )

    # 6. 创建普通用户
    normal_user = User.objects.create_user(
        username="delete_test_normal",
        password="Test123456",
    )

print("测试数据创建成功")