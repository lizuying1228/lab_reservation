from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class User(AbstractUser):
    phone = models.CharField(verbose_name="手机号", max_length=11, blank=True)

    def __str__(self) -> str:
        return self.username