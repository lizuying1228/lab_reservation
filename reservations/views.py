from reservations.models import Reservation
from reservations.serializers import (ReservationCreateSerializer, ReservationReviewSerializer, 
                                      ReservationSerializer)
from reservations.permissions import ReservationPermission
from reservations.services import review_reservation, cancel_reservation, create_reservation
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)
# Create your views here.
class ReservationViewSet(ModelViewSet):
    permission_classes = [ReservationPermission]
    filterset_fields = [ 
        "student",
        "reservationtime", 
        "reservationtime__lab",
        "reservationtime__date",
        "reservationtime__time",
        "status",
        ]
    
    search_fields = [
        "student__name",
        "student__student_no",
        "reservationtime__lab__lab_no",
        "reservationtime__lab__position",
    ]

    ordering_fields = [
        "id",
        "created_at",
        "status",
        "reservationtime__date",
        "reservationtime__time",
    ]

    ordering = ["id"]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Reservation.objects.select_related("student", "reservationtime", 
                                                      "student__user", "reservationtime__lab")
        
        elif hasattr(user, "labadmin"):
            return Reservation.objects.filter(
                    reservationtime__lab__labadmin__user = user).select_related(
                    "student", "reservationtime", "student__user", "reservationtime__lab")

        elif hasattr(user, "student"):
            return Reservation.objects.filter(student__user = user).select_related(
                "student", "reservationtime", "student__user", "reservationtime__lab")

        return Reservation.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return ReservationCreateSerializer

        elif self.action == "review":
            return ReservationReviewSerializer

        return ReservationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reservation = create_reservation(
            validated_data=serializer.validated_data,
            operator_id=request.user.id
        )

        response_serializer = ReservationSerializer(
            reservation,
            context=self.get_serializer_context()
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
        

    @action(detail=True, methods=["patch"], url_name="review", url_path="review")
    def review(self, request, pk=None):
        reservation = self.get_object()
        serializer = ReservationReviewSerializer(instance=reservation, data=request.data, context={"request": request})

        serializer.is_valid(raise_exception=True)
        target_status = serializer.validated_data["status"]
        result = review_reservation(reservation_id=reservation.id, target_status=target_status, operator_id=request.user.id)
        response_serializer = ReservationSerializer(result)

        return Response({"reservation": response_serializer.data}, status=status.HTTP_200_OK)


    @action(detail=True, methods=["patch"], url_name="cancel", url_path="cancel")
    def cancel(self, request, pk=None):
        reservation = self.get_object()

        result = cancel_reservation(reservation_id=reservation.id, operator_id=request.user.id)
        response_serializer = ReservationSerializer(result)

        return Response({"reservation": response_serializer.data}, status=status.HTTP_200_OK)

    