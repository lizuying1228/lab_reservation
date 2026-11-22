from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from lab_admins.models import LabAdmin
from labs.models import Laboratory
from reservation_times.models import ReservationTime
from reservations.models import Reservation
from students.models import Student

User = get_user_model()

# 1. 创建测试管理员
user = User.objects.create_user(
    username="delete_labadmin_test",
    password="Test123456",
)

labadmin = LabAdmin.objects.create(
    user=user,
    name="管理员软删除测试",
    admin_no="DELADMIN001",
    birth_date="1995-01-01",
)

# 2. 创建两个实验室
lab_a = Laboratory.objects.create(
    lab_no="DEL-LAB-A001",
    position="管理员删除测试实验室A",
    status=Laboratory.StatusChoices.OPEN,
    labadmin=labadmin,
)

lab_b = Laboratory.objects.create(
    lab_no="DEL-LAB-B001",
    position="管理员删除测试实验室B",
    status=Laboratory.StatusChoices.OPEN,
    labadmin=labadmin,
)

# 3. 创建两个预约时段
date = timezone.localdate() + timedelta(days=25)

slot_a = ReservationTime.objects.create(
    lab=lab_a,
    date=date,
    time="morning",
    status=ReservationTime.StatusChoices.OCCUPIED,
)

slot_b = ReservationTime.objects.create(
    lab=lab_b,
    date=date,
    time="afternoon",
    status=ReservationTime.StatusChoices.AVAILABLE,
)

# 4. 创建一条已通过预约
student = Student.objects.filter(is_deleted=False).first()
assert student is not None, "没有有效学生"

reservation = Reservation.objects.create(
    student=student,
    reservationtime=slot_a,
    status=Reservation.StatusChoices.APPROVED,
)

print("LabAdmin ID:", labadmin.id)
print("User ID:", user.id)
print("实验室 A ID:", lab_a.id)
print("实验室 B ID:", lab_b.id)
print("预约时段 A ID:", slot_a.id)
print("预约时段 B ID:", slot_b.id)
print("预约记录 ID:", reservation.id)