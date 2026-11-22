
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from students.models import Student
from lab_admins.models import LabAdmin
from labs.models import Laboratory
from reservation_times.models import ReservationTime
from reservations.models import Reservation

User = get_user_model()

PASSWORD = "Test123456"


@transaction.atomic
def create_test_data():
    # 1. 创建或获取用户，并统一设置测试密码
    def get_user(username):
        user, created = User.objects.get_or_create(
            username=username
        )

        if getattr(user, "is_deleted", False):
            raise ValueError(f"用户已经软删除：{username}")

        user.set_password(PASSWORD)
        user.save(update_fields=["password"])

        return user

    student_user_1 = get_user("res_stu_03_20261121")
    student_user_2 = get_user("res_stu_04_20261121")

    admin_user_1 = get_user("res_admin_03_20261121")
    admin_user_2 = get_user("res_admin_04_20261121")

    # 2. 创建学生档案
    student_1, _ = Student.objects.get_or_create(
        student_no="RS2026003",
        defaults={
            "user": student_user_1,
            "name": "张三",
            "birth_date": date(2005, 1, 1),
        },
    )

    student_2, _ = Student.objects.get_or_create(
        student_no="RS2026004",
        defaults={
            "user": student_user_2,
            "name": "李四",
            "birth_date": date(2005, 2, 1),
        },
    )

    if student_1.user_id != student_user_1.id or student_1.is_deleted:
        raise ValueError("张三的学生档案与测试账号不匹配或已软删除")

    if student_2.user_id != student_user_2.id or student_2.is_deleted:
        raise ValueError("李四的学生档案与测试账号不匹配或已软删除")

    # 3. 创建管理员档案
    admin_1, _ = LabAdmin.objects.get_or_create(
        admin_no="RA2026003",
        defaults={
            "user": admin_user_1,
            "name": "王老师",
            "birth_date": date(1980, 1, 1),
        },
    )

    admin_2, _ = LabAdmin.objects.get_or_create(
        admin_no="RA2026004",
        defaults={
            "user": admin_user_2,
            "name": "赵老师",
            "birth_date": date(1982, 1, 1),
        },
    )

    if admin_1.user_id != admin_user_1.id or admin_1.is_deleted:
        raise ValueError("王老师的管理员档案与测试账号不匹配或已软删除")

    if admin_2.user_id != admin_user_2.id or admin_2.is_deleted:
        raise ValueError("赵老师的管理员档案与测试账号不匹配或已软删除")

    # 4. 创建实验室
    lab_1, _ = Laboratory.objects.get_or_create(
        lab_no="RES-C301",
        defaults={
            "position": "教学楼 C301",
            "labadmin": admin_1,
            "status": Laboratory.StatusChoices.OPEN,
        },
    )

    lab_2, _ = Laboratory.objects.get_or_create(
        lab_no="RES-C302",
        defaults={
            "position": "教学楼 C302",
            "labadmin": admin_1,
            "status": Laboratory.StatusChoices.OPEN,
        },
    )

    lab_3, _ = Laboratory.objects.get_or_create(
        lab_no="RES-D401",
        defaults={
            "position": "实验楼 D401",
            "labadmin": admin_2,
            "status": Laboratory.StatusChoices.OPEN,
        },
    )

    if (
        lab_1.is_deleted or lab_1.labadmin_id != admin_1.id
        or lab_2.is_deleted or lab_2.labadmin_id != admin_1.id
        or lab_3.is_deleted or lab_3.labadmin_id != admin_2.id
    ):
        raise ValueError("实验室已软删除或负责人不匹配")

    # 5. 创建预约时段
    tomorrow = timezone.localdate() + timedelta(days=1)

    def get_time(lab, time_type):
        reservationtime, _ = ReservationTime.objects.get_or_create(
            lab=lab,
            date=tomorrow,
            time=time_type,
            defaults={
                "status": ReservationTime.StatusChoices.AVAILABLE,
            },
        )

        if reservationtime.is_deleted:
            raise ValueError(
                f"预约时段已软删除：{lab.lab_no} {time_type}"
            )

        return reservationtime

    time_conflict = get_time(lab_1, "morning")
    time_approved = get_time(lab_1, "afternoon")
    time_rejected = get_time(lab_2, "morning")
    time_api = get_time(lab_2, "afternoon")
    time_admin_2 = get_time(lab_3, "morning")

    # 6. 创建预约记录
    def get_reservation(student, reservationtime, initial_status):
        reservation, _ = Reservation.objects.get_or_create(
            student=student,
            reservationtime=reservationtime,
            defaults={
                "status": initial_status,
            },
        )
        return reservation

    get_reservation(
        student_1,
        time_conflict,
        Reservation.StatusChoices.PENDING,
    )

    get_reservation(
        student_2,
        time_conflict,
        Reservation.StatusChoices.PENDING,
    )

    approved_reservation = get_reservation(
        student_1,
        time_approved,
        Reservation.StatusChoices.APPROVED,
    )

    get_reservation(
        student_2,
        time_rejected,
        Reservation.StatusChoices.REJECTED,
    )

    get_reservation(
        student_2,
        time_admin_2,
        Reservation.StatusChoices.PENDING,
    )

    # 确保已通过的预约对应时段为 occupied
    if approved_reservation.status == Reservation.StatusChoices.APPROVED:
        time_approved.status = ReservationTime.StatusChoices.OCCUPIED
        time_approved.save(update_fields=["status"])

    print("测试数据创建或检查成功")
    print("预约日期：", tomorrow)
    print("学生 1：", student_user_1.username, student_1.name)
    print("学生 2：", student_user_2.username, student_2.name)
    print("管理员 1：", admin_user_1.username, admin_1.name)
    print("管理员 2：", admin_user_2.username, admin_2.name)


create_test_data()
