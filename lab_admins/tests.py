from django.urls import reverse
from rest_framework import status

from config.test_helpers import ProjectAPITestCase
from lab_admins.models import LabAdmin
from labs.models import Laboratory


class LabAdminAPITests(ProjectAPITestCase):
    def test_superuser_can_create_labadmin(self):
        root = self.make_user("root", superuser=True)
        self.login_as(root)
        response = self.client.post(reverse("labadmin-list"), {
            "name": "管理员甲", "admin_no": "A100", "birth_date": "1990-01-01",
            "username": "admin100", "password": "Pass12345",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        admin = LabAdmin.objects.get(admin_no="A100")
        self.assertTrue(admin.user.check_password("Pass12345"))

    def test_labadmin_can_only_view_and_update_own_profile(self):
        user, admin = self.make_labadmin()
        other_user, other = self.make_labadmin("admin2", "A002")
        self.login_as(user)
        self.assertEqual(self.client.get(reverse("labadmin-detail", args=[admin.id])).status_code,
                         status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("labadmin-detail", args=[other.id])).status_code,
                         status.HTTP_404_NOT_FOUND)
        response = self.client.patch(reverse("labadmin-detail", args=[admin.id]),
                                     {"name": "更新姓名"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        admin.refresh_from_db()
        self.assertEqual(admin.name, "更新姓名")

    def test_labadmin_cannot_create_or_delete_labadmin(self):
        user, admin = self.make_labadmin()
        self.login_as(user)
        create_response = self.client.post(reverse("labadmin-list"), {
            "name": "不允许", "admin_no": "A200", "birth_date": "1990-01-01",
            "username": "admin200", "password": "Pass12345",
        }, format="json")
        delete_response = self.client.delete(reverse("labadmin-detail", args=[admin.id]))
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_labadmin_soft_deletes_disables_user_and_unassigns_labs(self):
        root = self.make_user("root", superuser=True)
        user, admin = self.make_labadmin()
        lab = self.make_lab(admin)
        self.login_as(root)
        response = self.client.delete(reverse("labadmin-detail", args=[admin.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        admin.refresh_from_db(); user.refresh_from_db(); lab.refresh_from_db()
        self.assertTrue(admin.is_deleted)
        self.assertIsNotNone(admin.deleted_at)
        self.assertFalse(user.is_active)
        self.assertIsNone(lab.labadmin)
