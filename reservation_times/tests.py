from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from config.test_helpers import ProjectAPITestCase
from labs.models import Laboratory
from reservation_times.models import ReservationTime
from reservations.models import Reservation


class ReservationTimeAPITests(ProjectAPITestCase):
    def test_student_can_read_but_cannot_create_update_or_delete_times(self):
        student_user, _ = self.make_student()
        _, admin = self.make_labadmin()
        lab = self.make_lab(admin)
        item = self.make_time(lab)
        self.login_as(student_user)
        self.assertEqual(self.client.get(reverse("reservationtime-detail", args=[item.id])).status_code,
                         status.HTTP_200_OK)
        self.assertEqual(self.client.post(reverse("reservationtime-list"), {
            "lab_no": lab.lab_no, "date": str(timezone.localdate() + timedelta(days=3)), "time": "afternoon",
        }, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.patch(reverse("reservationtime-detail", args=[item.id]),
                                           {"time": "evening"}, format="json").status_code,
                         status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(reverse("reservationtime-detail", args=[item.id])).status_code,
                         status.HTTP_403_FORBIDDEN)

    def test_labadmin_can_create_only_for_owned_open_lab(self):
        user, admin = self.make_labadmin()
        _, other_admin = self.make_labadmin("admin2", "A002")
        own_lab = self.make_lab(admin)
        other_lab = self.make_lab(other_admin, "L002")
        self.login_as(user)
        payload = {"lab_no": own_lab.lab_no, "date": str(timezone.localdate() + timedelta(days=3)),
                   "time": "afternoon"}
        response = self.client.post(reverse("reservationtime-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload["lab_no"] = other_lab.lab_no
        denied = self.client.post(reverse("reservationtime-list"), payload, format="json")
        self.assertEqual(denied.status_code, status.HTTP_400_BAD_REQUEST)

    def test_labadmin_can_update_owned_unreserved_time_but_not_change_lab(self):
        user, admin = self.make_labadmin()
        lab = self.make_lab(admin)
        item = self.make_time(lab)
        self.login_as(user)
        response = self.client.patch(reverse("reservationtime-detail", args=[item.id]),
                                     {"time": "afternoon"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        denied = self.client.patch(reverse("reservationtime-detail", args=[item.id]),
                                   {"lab": lab.id}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reserved_time_cannot_be_updated_or_deleted(self):
        root = self.make_user("root", superuser=True)
        _, student = self.make_student()
        lab = self.make_lab()
        item = self.make_time(lab)
        Reservation.objects.create(student=student, reservationtime=item)
        self.login_as(root)
        update = self.client.patch(reverse("reservationtime-detail", args=[item.id]),
                                   {"time": "afternoon"}, format="json")
        delete = self.client.delete(reverse("reservationtime-detail", args=[item.id]))
        self.assertEqual(update.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(delete.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_superuser_can_delete_unreserved_time(self):
        user, admin = self.make_labadmin()
        lab = self.make_lab(admin)
        item = self.make_time(lab)
        self.login_as(user)
        self.assertEqual(self.client.delete(reverse("reservationtime-detail", args=[item.id])).status_code,
                         status.HTTP_403_FORBIDDEN)
        root = self.make_user("root", superuser=True)
        self.login_as(root)
        response = self.client.delete(reverse("reservationtime-detail", args=[item.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        item.refresh_from_db()
        self.assertTrue(item.is_deleted)

    def test_create_rejects_past_or_today_and_closed_lab(self):
        root = self.make_user("root", superuser=True)
        lab = self.make_lab()
        closed_lab = self.make_lab(lab_no="L002", status=Laboratory.StatusChoices.CLOSED)
        self.login_as(root)
        today = self.client.post(reverse("reservationtime-list"), {
            "lab_no": lab.lab_no, "date": str(timezone.localdate()), "time": "morning",
        }, format="json")
        closed = self.client.post(reverse("reservationtime-list"), {
            "lab_no": closed_lab.lab_no, "date": str(timezone.localdate() + timedelta(days=2)),
            "time": "morning",
        }, format="json")
        self.assertEqual(today.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(closed.status_code, status.HTTP_400_BAD_REQUEST)
