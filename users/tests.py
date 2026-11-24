from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from config.test_helpers import ProjectAPITestCase
from users.models import User
from students.models import Student
from lab_admins.models import LabAdmin
from labs.models import Laboratory


class UserAPITests(ProjectAPITestCase):
    def test_register_success_and_password_is_hashed(self):
        response = self.client.post(reverse("user-register"), {
            "username": "new_user", "password": "Pass12345",
            "email": "new@example.com", "phone": "12345678901",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="new_user")
        self.assertTrue(user.check_password("Pass12345"))
        self.assertNotEqual(user.password, "Pass12345")

    def test_register_rejects_duplicate_username_and_short_password(self):
        self.make_user("taken")
        duplicate = self.client.post(reverse("user-register"), {
            "username": "taken", "password": "Pass12345",
        }, format="json")
        short = self.client.post(reverse("user-register"), {
            "username": "another", "password": "123",
        }, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(short.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_can_read_and_update_email_phone_but_not_username(self):
        user = self.make_user("profile_user")
        self.login_as(user)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(reverse("profile"), {
            "username": "changed", "email": "a@example.com", "phone": "12345678901",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.username, "profile_user")
        self.assertEqual(user.email, "a@example.com")
        self.assertEqual(user.phone, "12345678901")

    def test_user_list_is_superuser_only(self):
        student_user, _ = self.make_student()
        self.login_as(student_user)
        self.assertEqual(self.client.get(reverse("user")).status_code,
                         status.HTTP_403_FORBIDDEN)
        superuser = self.make_user("root", superuser=True)
        self.login_as(superuser)
        self.assertEqual(self.client.get(reverse("user")).status_code,
                         status.HTTP_200_OK)

    def test_delete_student_user_soft_deletes_profile_and_disables_account(self):
        superuser = self.make_user("root", superuser=True)
        student_user, student = self.make_student()
        self.login_as(superuser)
        response = self.client.delete(reverse("user-delete", args=[student_user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        student.refresh_from_db()
        student_user.refresh_from_db()
        self.assertTrue(student.is_deleted)
        self.assertFalse(student_user.is_active)
        self.assertTrue(student_user.is_deleted)
        self.assertIsNotNone(student_user.deleted_at)

    def test_delete_labadmin_user_soft_deletes_profile_disables_user_and_unassigns_labs(self):
        superuser = self.make_user("root", superuser=True)
        admin_user, admin = self.make_labadmin()
        lab = self.make_lab(admin)
        self.login_as(superuser)
        response = self.client.delete(reverse("user-delete", args=[admin_user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        admin.refresh_from_db()
        admin_user.refresh_from_db()
        lab.refresh_from_db()
        self.assertTrue(admin.is_deleted)
        self.assertFalse(admin_user.is_active)
        self.assertTrue(admin_user.is_deleted)
        self.assertIsNone(lab.labadmin)

    def test_superuser_cannot_be_deleted(self):
        root = self.make_user("root", superuser=True)
        self.login_as(root)
        response = self.client.delete(reverse("user-delete", args=[root.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        root.refresh_from_db()
        self.assertFalse(root.is_deleted)

    def test_logout_blacklists_own_refresh_token(self):
        user = self.make_user("logout_user")
        self.login_as(user)
        refresh = str(RefreshToken.for_user(user))
        response = self.client.post(reverse("user-logout"), {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
