from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your models here.
class LabAdmin(models.Model):
    class Meta:
        verbose_name = "实验室管理员"
        verbose_name_plural = "实验室管理员"
        
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="labadmin", verbose_name="用户")
    name = models.CharField(max_length=50, blank=False, null=False, verbose_name="姓名")
    admin_no = models.CharField(max_length=20, blank=False, null=False, unique=True, verbose_name="管理编号")
    birth_date = models.DateField(blank=False, null=False, verbose_name="出生日期")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name="删除时间")

    def __str__(self):
        return self.name
