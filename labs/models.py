from django.db import models
from lab_admins.models import LabAdmin

# Create your models here.
class Laboratory(models.Model):
    class StatusChoices(models.TextChoices):
        OPEN = "open", "开放"
        CLOSED = "closed", "关闭"
        MAINTENANCE = "maintenance", "维修"

    lab_no = models.CharField(unique=True, max_length=20, blank=False, null=False, verbose_name="实验室编号")
    position = models.CharField(max_length=50, blank=False, null=False, verbose_name="实验室地点")
    labadmin = models.ForeignKey(LabAdmin, on_delete=models.SET_NULL, related_name="labs", 
                                 blank=True, null=True, verbose_name="实验室管理员")
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.OPEN, verbose_name="状态")

    def __str__(self):
        return self.lab_no
    