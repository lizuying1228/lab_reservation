from datetime import timedelta
from django.utils import timezone

from labs.models import Laboratory
from reservation_times.models import ReservationTime
from reservations.models import Reservation
from students.models import Student

student = Student.objects.filter(is_deleted=False).first()
assert student is not None, "没有有效学生"

labadmin = None
lab = Laboratory.objects.filter(
    is_deleted=False,
    status=Laboratory.StatusChoices.OPEN,
).first()

assert lab is not None, "没有开放实验室"

date = timezone.localdate() + timedelta(days=25)

# 实验室 A：没有预约记录
lab_a = Laboratory.objects.create(
    lab_no="DEL-A001",
    position="软删除测试实验室A",
    status=Laboratory.StatusChoices.OPEN,
    labadmin=lab.labadmin,
)

slot_a1 = ReservationTime.objects.create(
    lab=lab_a, date=date, time="morning"
)
slot_a2 = ReservationTime.objects.create(
    lab=lab_a, date=date, time="afternoon"
)

# 实验室 B：存在已取消预约记录
lab_b = Laboratory.objects.create(
    lab_no="DEL-B001",
    position="软删除测试实验室B",
    status=Laboratory.StatusChoices.OPEN,
    labadmin=lab.labadmin,
)

slot_b1 = ReservationTime.objects.create(
    lab=lab_b, date=date, time="morning"
)
slot_b2 = ReservationTime.objects.create(
    lab=lab_b, date=date, time="afternoon"
)

Reservation.objects.create(
    student=student,
    reservationtime=slot_b1,
    status=Reservation.StatusChoices.CANCELLED,
)

print("实验室 A:", lab_a.id)
print("实验室 B:", lab_b.id)
print("A 时段:", slot_a1.id, slot_a2.id)
print("B 时段:", slot_b1.id, slot_b2.id)