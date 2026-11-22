from datetime import timedelta
from django.utils import timezone
from labs.models import Laboratory
from reservation_times.models import ReservationTime
from reservations.models import Reservation
from students.models import Student

# 找一个有效学生和开放实验室
student = Student.objects.filter(is_deleted=False).first()
lab = Laboratory.objects.filter(
    is_deleted=False,
    status=Laboratory.StatusChoices.OPEN,
).first()

assert student is not None, "没有有效学生"
assert lab is not None, "没有开放实验室"

# 创建两个时段
date = timezone.localdate() + timedelta(days=20)

slot_free = ReservationTime.objects.create(
    lab=lab,
    date=date,
    time="morning",
)

slot_used = ReservationTime.objects.create(
    lab=lab,
    date=date,
    time="afternoon",
)

# 给第二个时段创建一条已取消预约
reservation = Reservation.objects.create(
    student=student,
    reservationtime=slot_used,
    status=Reservation.StatusChoices.CANCELLED,
)

print("无预约时段 ID:", slot_free.id)
print("有预约时段 ID:", slot_used.id)
print("关联预约 ID:", reservation.id)