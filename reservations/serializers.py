from reservations.models import Reservation
from reservation_times.models import ReservationTime
from labs.models import Laboratory
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

class ReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["reservationtime_id"]

    reservationtime_id = serializers.IntegerField(required=True, write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not hasattr(user, "student"):
            raise serializers.ValidationError({"Error": "该账户不是学生"})
        
        reservationtime_id = attrs.get("reservationtime_id")
        try:
            reservationtime = ReservationTime.objects.get(id = reservationtime_id, is_deleted=False)
        except ReservationTime.DoesNotExist:
            raise serializers.ValidationError({"Error": "预约时段不存在"})

        if reservationtime.lab.is_deleted or reservationtime.lab.status != Laboratory.StatusChoices.OPEN:
            raise serializers.ValidationError({"Error": "预约实验室不存在或者未开放"})

        if reservationtime.date <= timezone.localdate():
            raise serializers.ValidationError({"Error": "预约日期必须从明天开始"})

        if reservationtime.status != ReservationTime.StatusChoices.AVAILABLE:
            raise serializers.ValidationError({"Error": "预约时间已被占用"})

        exists = Reservation.objects.filter(student=user.student, reservationtime=reservationtime).exists()
        if exists:
            raise serializers.ValidationError({"Error": "该账户已预约过此时间段"})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user
        student = user.student
        reservationtime_id = validated_data.pop("reservationtime_id")
        reservationtime = ReservationTime.objects.get(id = reservationtime_id, is_deleted=False,
                                                      lab__is_deleted=False)
        return Reservation.objects.create(student=student, reservationtime=reservationtime)


class ReservationReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            Reservation.StatusChoices.APPROVED,
            Reservation.StatusChoices.REJECTED
        ]
    )

    def validate(self, attrs):
        user = self.context["request"].user
        if not (user.is_superuser or hasattr(user, "labadmin")):
            raise serializers.ValidationError({"Error": "非管理员不允许审核"})

        reservation = self.instance
        reservationtime = reservation.reservationtime
        current_status = reservation.status

        lab = getattr(reservationtime, 'lab', None)
        if lab is None or lab.is_deleted:
            raise serializers.ValidationError({"Error": "该实验室已停用"})
        
        target_admin = getattr(lab, 'labadmin', None)
        
        if hasattr(user, "labadmin") and user.labadmin != target_admin:
            raise serializers.ValidationError({"Error": "非该实验室管理员不允许审核"})

        if current_status != Reservation.StatusChoices.PENDING:
            raise serializers.ValidationError({"Error": "该预约不是待审核"})

        return attrs 


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["id", "student", "reservationtime", "status", "created_at"]
        read_only_fields = fields






        
            

