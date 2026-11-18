from django.db import models
from students.models import Student
from reservation_times.models import ReservationTime

# Create your models here.
class Reservation(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = ["student", "reservationtime"],
                name = "unique_reservation"
            )
        ]

    class StatusChoices(models.TextChoices):
        PENDING = "pending", "待审核"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已拒绝"
        CANCELLED = "cancelled", "已取消"

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="reservations", verbose_name="学生")
    reservationtime = models.ForeignKey(ReservationTime, on_delete=models.PROTECT, related_name="reservations", verbose_name="预约")
    status = models.CharField(max_length=20, blank=False, null=False, 
                              choices=StatusChoices.choices, default=StatusChoices.PENDING, verbose_name="预约状态")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = self.get_status_display()
        return f"{self.student} - {self.reservationtime} - {status}"
