from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from config.test_helpers import ProjectAPITestCase
from labs.models import Laboratory
from reservations.models import Reservation
from reservation_times.models import ReservationTime


class LaboratoryAPITests(ProjectAPITestCase):
    def test_student_can_read_labs_but_cannot_modify(self):
        student_user, _ = self.make_student()
        lab = self.make_lab()
        self.login_as(student_user)
        self.assertEqual(self.client.get(reverse("lab-detail", args=[lab.id])).status_code,
                         status.HTTP_200_OK)
        self.assertEqual(self.client.patch(reverse("lab-detail", args=[lab.id]),
                                           {"position": "新地点"}, format="json").status_code,
                         status.HTTP_403_FORBIDDEN)

    def test_labadmin_can_only_view_and_patch_owned_lab(self):
        user, admin = self.make_labadmin()
        _, other_admin = self.make_labadmin("admin2", "A002")
        own_lab = self.make_lab(admin)
        other_lab = self.make_lab(other_admin, "L002")
        self.login_as(user)
        response = self.client.patch(reverse("lab-detail", args=[own_lab.id]),
                                     {"position": "新地点"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("lab-detail", args=[other_lab.id])).status_code,
                         status.HTTP_404_NOT_FOUND)
        forbidden_field = self.client.patch(reverse("lab-detail", args=[own_lab.id]),
                                            {"labadmin": other_admin.id}, format="json")
        self.assertEqual(forbidden_field.status_code, status.HTTP_400_BAD_REQUEST)

    def test_superuser_can_create_lab(self):
        root = self.make_user("root", superuser=True)
        _, admin = self.make_labadmin()
        self.login_as(root)
        response = self.client.post(reverse("lab-list"), {
            "lab_no": "L100", "position": "二号楼", "labadmin_admin_no": admin.admin_no,
            "status": Laboratory.StatusChoices.OPEN,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Laboratory.objects.filter(lab_no="L100", labadmin=admin).exists())

    def test_status_change_is_rejected_when_any_reservation_exists(self):
        root = self.make_user("root", superuser=True)
        _, student = self.make_student()
        _, admin = self.make_labadmin()
        lab = self.make_lab(admin)
        reservation_time = self.make_time(lab)
        Reservation.objects.create(student=student, reservationtime=reservation_time)
        self.login_as(root)
        response = self.client.patch(reverse("lab-detail", args=[lab.id]),
                                     {"status": Laboratory.StatusChoices.CLOSED}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        lab.refresh_from_db()
        self.assertEqual(lab.status, Laboratory.StatusChoices.OPEN)

    def test_status_can_change_without_reservations(self):
        root = self.make_user("root", superuser=True)
        lab = self.make_lab()
        self.login_as(root)
        response = self.client.patch(reverse("lab-detail", args=[lab.id]),
                                     {"status": Laboratory.StatusChoices.CLOSED}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lab.refresh_from_db()
        self.assertEqual(lab.status, Laboratory.StatusChoices.CLOSED)

    def test_lab_cannot_be_deleted_if_reservation_exists(self):
        root = self.make_user("root", superuser=True)
        _, student = self.make_student()
        lab = self.make_lab()
        reservation_time = self.make_time(lab)
        Reservation.objects.create(student=student, reservationtime=reservation_time)
        self.login_as(root)
        response = self.client.delete(reverse("lab-detail", args=[lab.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        lab.refresh_from_db()
        self.assertFalse(lab.is_deleted)

    def test_lab_delete_soft_deletes_its_reservation_times(self):
        root = self.make_user("root", superuser=True)
        lab = self.make_lab()
        reservation_time = self.make_time(lab)
        self.login_as(root)
        response = self.client.delete(reverse("lab-detail", args=[lab.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        lab.refresh_from_db(); reservation_time.refresh_from_db()
        self.assertTrue(lab.is_deleted)
        self.assertTrue(reservation_time.is_deleted)
