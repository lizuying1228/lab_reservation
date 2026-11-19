from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your models here.
class Student(models.Model):
    class Meta:
        verbose_name = "学生"
        verbose_name_plural = "学生"
      
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student", verbose_name="用户")
    name = models.CharField(max_length=50, blank=False, null=False, verbose_name="姓名")
    student_no = models.CharField(max_length=20, unique=True, blank=False, null=False, verbose_name="学号")
    birth_date = models.DateField(blank=False, null=False, verbose_name="出生日期")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name="删除时间")

    def __str__(self) -> str:
        return self.name