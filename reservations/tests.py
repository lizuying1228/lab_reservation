from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from config.test_helpers import ProjectAPITestCase
from labs.models import Laboratory
from reservation_times.models import ReservationTime
from reservations.models import Reservation


class ReservationAPITests(ProjectAPITestCase):
    def setUp(self):
        self.student_user, self.student = self.make_student()
        self.admin_user, self.admin = self.make_labadmin()
        self.other_admin_user, self.other_admin = self.make_labadmin("admin2", "A002")
        self.lab = self.make_lab(self.admin)
        self.other_lab = self.make_lab(self.other_admin, "L002")
        self.item = self.make_time(self.lab)

    def test_student_can_create_reservation(self):
        self.login_as(self.student_user)
        response = self.client.post(reverse("reservation-list"),
                                    {"reservationtime_id": self.item.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Reservation.objects.filter(student=self.student, reservationtime=self.item,
                                                   status=Reservation.StatusChoices.PENDING).exists())

    def test_student_cannot_book_today_or_more_than_seven_days_ahead(self):
        self.login_as(self.student_user)
        today = self.make_time(self.lab, date=timezone.localdate(), time=ReservationTime.TimeChoices.AFTERNOON)
        too_far = self.make_time(self.lab, date=timezone.localdate() + timedelta(days=8),
                                 time=ReservationTime.TimeChoices.AFTERNOON)
        today_response = self.client.post(reverse("reservation-list"),
                                          {"reservationtime_id": today.id}, format="json")
        far_response = self.client.post(reverse("reservation-list"),
                                        {"reservationtime_id": too_far.id}, format="json")
        self.assertEqual(today_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(far_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_cannot_book_closed_or_occupied_time(self):
        self.login_as(self.student_user)
        closed_lab = self.make_lab(self.admin, "L003", Laboratory.StatusChoices.CLOSED)
        closed_time = self.make_time(closed_lab)
        occupied_time = self.make_time(self.lab, time=ReservationTime.TimeChoices.AFTERNOON,
                                       status=ReservationTime.StatusChoices.OCCUPIED)
        closed_response = self.client.post(reverse("reservation-list"),
                                           {"reservationtime_id": closed_time.id}, format="json")
        occupied_response = self.client.post(reverse("reservation-list"),
                                             {"reservationtime_id": occupied_time.id}, format="json")
        self.assertEqual(closed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(occupied_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_student_cannot_reserve_same_time_twice_even_after_cancelled(self):
        Reservation.objects.create(student=self.student, reservationtime=self.item,
                                   status=Reservation.StatusChoices.CANCELLED)
        self.login_as(self.student_user)
        response = self.client.post(reverse("reservation-list"),
                                    {"reservationtime_id": self.item.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_sees_only_own_reservations_and_can_cancel_own_pending(self):
        own = Reservation.objects.create(student=self.student, reservationtime=self.item)
        _, other_student = self.make_student("student2", "S002")
        other_time = self.make_time(self.other_lab)
        other = Reservation.objects.create(student=other_student, reservationtime=other_time)
        self.login_as(self.student_user)
        response = self.client.get(reverse("reservation-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(own.id, ids)
        self.assertNotIn(other.id, ids)
        cancel = self.client.patch(reverse("reservation-cancel", args=[own.id]), {}, format="json")
        self.assertEqual(cancel.status_code, status.HTTP_200_OK)
        own.refresh_from_db()
        self.assertEqual(own.status, Reservation.StatusChoices.CANCELLED)

    def test_labadmin_can_review_only_own_lab_reservations(self):
        own = Reservation.objects.create(student=self.student, reservationtime=self.item)
        other_time = self.make_time(self.other_lab)
        other = Reservation.objects.create(student=self.student, reservationtime=other_time)
        self.login_as(self.admin_user)
        response = self.client.patch(reverse("reservation-review", args=[own.id]),
                                     {"status": "approved"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.patch(reverse("reservation-review", args=[other.id]),
                                           {"status": "approved"}, format="json").status_code,
                         status.HTTP_404_NOT_FOUND)
        own.refresh_from_db(); self.item.refresh_from_db()
        self.assertEqual(own.status, Reservation.StatusChoices.APPROVED)
        self.assertEqual(self.item.status, ReservationTime.StatusChoices.OCCUPIED)

    def test_rejection_does_not_occupy_time(self):
        reservation = Reservation.objects.create(student=self.student, reservationtime=self.item)
        self.login_as(self.admin_user)
        response = self.client.patch(reverse("reservation-review", args=[reservation.id]),
                                     {"status": "rejected"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db(); self.item.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.StatusChoices.REJECTED)
        self.assertEqual(self.item.status, ReservationTime.StatusChoices.AVAILABLE)

    def test_only_pending_reservation_can_be_reviewed(self):
        reservation = Reservation.objects.create(student=self.student, reservationtime=self.item,
                                                 status=Reservation.StatusChoices.CANCELLED)
        self.login_as(self.admin_user)
        response = self.client.patch(reverse("reservation-review", args=[reservation.id]),
                                     {"status": "approved"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approved_reservation_can_be_cancelled_before_start_and_releases_time(self):
        approved_time = self.make_time(
            self.lab, date=timezone.localdate() + timedelta(days=3),
            time=ReservationTime.TimeChoices.EVENING,
            status=ReservationTime.StatusChoices.OCCUPIED,
        )
        reservation = Reservation.objects.create(
            student=self.student, reservationtime=approved_time,
            status=Reservation.StatusChoices.APPROVED,
        )
        self.login_as(self.student_user)
        response = self.client.patch(
            reverse("reservation-cancel", args=[reservation.id]), {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db(); approved_time.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.StatusChoices.CANCELLED)
        self.assertEqual(approved_time.status, ReservationTime.StatusChoices.AVAILABLE)

    def test_approved_reservation_cannot_be_cancelled_after_start(self):
        today_time = self.make_time(self.lab, date=timezone.localdate(),
                                    time=ReservationTime.TimeChoices.MORNING,
                                    status=ReservationTime.StatusChoices.OCCUPIED)
        reservation = Reservation.objects.create(student=self.student, reservationtime=today_time,
                                                 status=Reservation.StatusChoices.APPROVED)
        self.login_as(self.student_user)
        future_after_start = timezone.now() + timedelta(days=1)
        with patch("reservations.services.timezone.now", return_value=future_after_start):
            response = self.client.patch(reverse("reservation-cancel", args=[reservation.id]), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.StatusChoices.APPROVED)

    def test_labadmin_cannot_create_reservation(self):
        self.login_as(self.admin_user)
        response = self.client.post(reverse("reservation-list"),
                                    {"reservationtime_id": self.item.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
