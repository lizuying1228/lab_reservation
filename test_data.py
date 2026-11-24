
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

today = timezone.localdate()
tomorrow = today + timedelta(days=1)
day_7 = today + timedelta(days=7)
day_8 = today + timedelta(days=8)

@transaction.atomic
def create_test_data():
    # 1. 获取现有 Superuser；如果没有则创建一个
    superuser = User.objects.filter(
        is_superuser=True,
        is_active=True,
        is_deleted=False,
    ).first()

    if superuser is None:
        superuser = User.objects.create_superuser(
            username="test_root",
            password="Root123!",
            email="",
        )
        print("创建 Superuser：test_root / Root123!")

    # 2. 创建或获取测试用户
    def get_test_user(username, password):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "is_active": True,
                "is_deleted": False,
            },
        )

        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        else:
            user.set_password(password)
            user.is_active = True
            user.is_deleted = False
            user.save(update_fields=[
                "password",
                "is_active",
                "is_deleted",
            ])

        return user

    # 3. 创建两个学生账号
    student_user_1 = get_test_user(
        "test_student_01",
        "Student123!",
    )

    student_user_2 = get_test_user(
        "test_student_02",
        "Student123!",
    )

    student_1, _ = Student.objects.update_or_create(
        user=student_user_1,
        defaults={
            "name": "测试学生一",
            "student_no": "TST2026001",
            "birth_date": date(2000, 1, 1),
            "is_deleted": False,
            "deleted_at": None,
        },
    )

    student_2, _ = Student.objects.update_or_create(
        user=student_user_2,
        defaults={
            "name": "测试学生二",
            "student_no": "TST2026002",
            "birth_date": date(2001, 1, 1),
            "is_deleted": False,
            "deleted_at": None,
        },
    )

    # 4. 创建实验室管理员
    labadmin_user = get_test_user(
        "test_labadmin_01",
        "LabAdmin123!",
    )

    labadmin, _ = LabAdmin.objects.update_or_create(
        user=labadmin_user,
        defaults={
            "name": "测试实验室管理员",
            "admin_no": "ADMTEST001",
            "birth_date": date(1990, 1, 1),
            "is_deleted": False,
            "deleted_at": None,
        },
    )

    # 5. 创建测试实验室
    lab, _ = Laboratory.objects.update_or_create(
        lab_no="TESTLAB001",
        defaults={
            "position": "测试楼 101",
            "labadmin": labadmin,
            "status": Laboratory.StatusChoices.OPEN,
            "is_deleted": False,
            "deleted_at": None,
        },
    )

    # 如果之前已经测试过这个实验室，不要覆盖历史预约数据
    if Reservation.objects.filter(
        reservationtime__lab=lab
    ).exists():
        raise RuntimeError(
            "测试实验室已有预约记录，请勿重置其预约时段状态。"
            "请先检查旧测试数据，或使用新的实验室编号。"
        )

    # 6. 创建六个测试预约时段
    test_slots = [
        (today, ReservationTime.TimeChoices.MORNING, "今天"),
        (tomorrow, ReservationTime.TimeChoices.MORNING, "明天"),
        (tomorrow, ReservationTime.TimeChoices.AFTERNOON, "明天下午"),
        (tomorrow, ReservationTime.TimeChoices.EVENING, "明天晚上"),
        (day_7, ReservationTime.TimeChoices.MORNING, "第七天"),
        (day_8, ReservationTime.TimeChoices.MORNING, "第八天"),
    ]

    for slot_date, slot_time, label in test_slots:
        ReservationTime.objects.update_or_create(
            lab=lab,
            date=slot_date,
            time=slot_time,
            defaults={
                "status": ReservationTime.StatusChoices.AVAILABLE,
                "is_deleted": False,
                "deleted_at": None,
            },
        )
        print(
            f"{label}: {slot_date} {slot_time}"
        )

    print("\n========== 测试数据创建完成 ==========")
    print("Superuser:", superuser.username)
    print("Student 1:", student_user_1.username, "/ Student123!")
    print("Student 2:", student_user_2.username, "/ Student123!")
    print("LabAdmin:", labadmin_user.username, "/ LabAdmin123!")
    print("Laboratory:", lab.lab_no)
    print("Student IDs:", student_1.id, student_2.id)
    print("LabAdmin ID:", labadmin.id)
    print("Laboratory ID:", lab.id)

create_test_data()
print("\n========== 学生 ==========")

for student in Student.objects.filter(
    student_no__startswith="TST2026"
):
    print(
        student.id,
        student.student_no,
        student.user.username,
    )

print("\n========== 实验室 ==========")

print(lab.id, lab.lab_no, lab.status)

print("\n========== 预约时段 ==========")

for slot in ReservationTime.objects.filter(
    lab=lab
).order_by("date", "time"):
    print(
        slot.id,
        slot.date,
        slot.time,
        slot.status,
        "deleted=", slot.is_deleted,
    )