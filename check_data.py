from reservation_times.models import ReservationTime
from labs.models import Laboratory

lab = Laboratory.objects.get(lab_no="TESTLAB001")

print("\n========== 实验室 ==========")
print(lab.id, lab.lab_no, lab.status)

print("\n========== 预约时段 ==========")

for slot in ReservationTime.objects.filter(
    lab=lab,
    is_deleted=False,
).order_by("date", "time"):
    print(
        slot.id,
        slot.date,
        slot.time,
        slot.status,
    )