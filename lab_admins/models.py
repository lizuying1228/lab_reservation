from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your models here.
class LabAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="labadmin", verbose_name="用户")
    name = models.CharField(max_length=50, blank=False, null=False, verbose_name="姓名")
    admin_no = models.CharField(max_length=20, blank=False, null=False, unique=True, verbose_name="管理编号")
    birth_date = models.DateField(blank=False, null=False, verbose_name="出生日期")

    def __str__(self):
        return self.name
