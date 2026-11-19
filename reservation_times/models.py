from django.db import models
from labs.models import Laboratory
from django.db.models import UniqueConstraint
# Create your models here.
class ReservationTime(models.Model):

    class Meta:
        constraints = [
            UniqueConstraint(
                fields = ["lab", "date", "time"],
                name = "unique_reservation_time"
            )
        ]

        verbose_name = "预约时间"
        verbose_name_plural = "预约时间"

    class TimeChoices(models.TextChoices):
        MORNING = "morning", "上午"
        AFTERNOON = "afternoon", "下午"
        EVENING = "evening", "晚上"

    class StatusChoices(models.TextChoices):
        AVAILABLE = "available", "可预约"
        OCCUPIED = "occupied", "已占用"

    lab = models.ForeignKey(Laboratory, on_delete=models.PROTECT, related_name="reservation_times", verbose_name="实验室")
    date = models.DateField(blank=False, null=False, verbose_name="预约日期")
    time = models.CharField(max_length=30, blank=False, null=False, choices=TimeChoices.choices, verbose_name="预约时间")
    status = models.CharField(max_length=30, blank=False, null=False, 
                              choices=StatusChoices.choices, default=StatusChoices.AVAILABLE, verbose_name="预约状态")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name="删除时间")

    def __str__(self) -> str:
        time = self.get_time_display()
        status = self.get_status_display()
        return f"{self.lab} - {self.date} - {time} - {status}"