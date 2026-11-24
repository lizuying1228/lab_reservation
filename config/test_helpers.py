from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from students.models import Student
from lab_admins.models import LabAdmin
from labs.models import Laboratory
from reservation_times.models import ReservationTime

User = get_user_model()


class ProjectAPITestCase(APITestCase):
    """各应用 API 测试共用的账号和业务数据工厂。"""

    def make_user(self, username, *, superuser=False, password="Pass12345"):
        if superuser:
            return User.objects.create_superuser(
                username=username, password=password, email=f"{username}@example.com"
            )
        return User.objects.create_user(username=username, password=password)

    def make_student(self, username="student1", student_no="S001"):
        user = self.make_user(username)
        student = Student.objects.create(
            user=user, name="测试学生", student_no=student_no,
            birth_date=timezone.localdate() - timedelta(days=365 * 20),
        )
        return user, student

    def make_labadmin(self, username="admin1", admin_no="A001"):
        user = self.make_user(username)
        admin = LabAdmin.objects.create(
            user=user, name="测试管理员", admin_no=admin_no,
            birth_date=timezone.localdate() - timedelta(days=365 * 30),
        )
        return user, admin

    def make_lab(self, labadmin=None, lab_no="L001", status=Laboratory.StatusChoices.OPEN):
        return Laboratory.objects.create(
            lab_no=lab_no, position="一号楼101", labadmin=labadmin, status=status
        )

    def make_time(self, lab, *, date=None, time=ReservationTime.TimeChoices.MORNING,
                  status=ReservationTime.StatusChoices.AVAILABLE):
        return ReservationTime.objects.create(
            lab=lab, date=date or (timezone.localdate() + timedelta(days=2)),
            time=time, status=status,
        )

    def login_as(self, user):
        self.client.force_authenticate(user=user)
