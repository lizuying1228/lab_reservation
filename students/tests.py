from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from config.test_helpers import ProjectAPITestCase
from students.models import Student
from reservations.models import Reservation
from reservation_times.models import ReservationTime


class StudentAPITests(ProjectAPITestCase):
    def test_student_can_only_view_and_update_own_profile(self):
        user, student = self.make_student()
        other_user, other = self.make_student("student2", "S002")
        self.login_as(user)
        response = self.client.get(reverse("student-detail", args=[student.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("student-detail", args=[other.id])).status_code,
                         status.HTTP_404_NOT_FOUND)
        response = self.client.patch(reverse("student-detail", args=[student.id]),
                                     {"name": "新名字"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        student.refresh_from_db()
        self.assertEqual(student.name, "新名字")

    def test_labadmin_can_read_students_but_cannot_modify_them(self):
        admin_user, _ = self.make_labadmin()
        _, student = self.make_student()
        self.login_as(admin_user)
        self.assertEqual(self.client.get(reverse("student-detail", args=[student.id])).status_code,
                         status.HTTP_200_OK)
        self.assertEqual(self.client.patch(reverse("student-detail", args=[student.id]),
                                           {"name": "修改"}, format="json").status_code,
                         status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(reverse("student-detail", args=[student.id])).status_code,
                         status.HTTP_403_FORBIDDEN)

    def test_superuser_can_create_student_with_new_account(self):
        root = self.make_user("root", superuser=True)
        self.login_as(root)
        response = self.client.post(reverse("student-list"), {
            "name": "新学生", "student_no": "S100", "birth_date": "2005-01-01",
            "username": "new_student", "password": "Pass12345",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        student = Student.objects.get(student_no="S100")
        self.assertTrue(student.user.check_password("Pass12345"))

    def test_superuser_can_bind_existing_unbound_user(self):
        root = self.make_user("root", superuser=True)
        unbound = self.make_user("unbound")
        self.login_as(root)
        response = self.client.post(reverse("student-list"), {
            "name": "绑定学生", "student_no": "S101", "birth_date": "2005-01-01",
            "user_id": unbound.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Student.objects.get(student_no="S101").user_id, unbound.id)

    def test_student_creation_rejects_user_already_bound_to_labadmin(self):
        root = self.make_user("root", superuser=True)
        admin_user, _ = self.make_labadmin()
        self.login_as(root)
        response = self.client.post(reverse("student-list"), {
            "name": "错误绑定", "student_no": "S102", "birth_date": "2005-01-01",
            "user_id": admin_user.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_student_cancels_pending_and_approved_reservations_and_releases_time(self):
        root = self.make_user("root", superuser=True)
        student_user, student = self.make_student()
        admin_user, admin = self.make_labadmin()
        lab = self.make_lab(admin)
        pending_time = self.make_time(lab, date=timezone.localdate() + timedelta(days=2))
        approved_time = self.make_time(lab, date=timezone.localdate() + timedelta(days=3),
                                       time=ReservationTime.TimeChoices.AFTERNOON,
                                       status=ReservationTime.StatusChoices.OCCUPIED)
        pending = Reservation.objects.create(student=student, reservationtime=pending_time)
        approved = Reservation.objects.create(student=student, reservationtime=approved_time,
                                              status=Reservation.StatusChoices.APPROVED)
        self.login_as(root)
        response = self.client.delete(reverse("student-detail", args=[student.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        student.refresh_from_db(); student_user.refresh_from_db()
        pending.refresh_from_db(); approved.refresh_from_db(); approved_time.refresh_from_db()
        self.assertTrue(student.is_deleted)
        self.assertFalse(student_user.is_active)
        self.assertEqual(pending.status, Reservation.StatusChoices.CANCELLED)
        self.assertEqual(approved.status, Reservation.StatusChoices.CANCELLED)
        self.assertEqual(approved_time.status, ReservationTime.StatusChoices.AVAILABLE)
