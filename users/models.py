from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
        
    phone = models.CharField(verbose_name="手机号", max_length=11, blank=True)
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="删除时间")

    def __str__(self) -> str:
        return self.username