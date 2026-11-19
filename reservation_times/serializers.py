from reservation_times.models import ReservationTime
from labs.models import Laboratory
from rest_framework import serializers  
from django.db import transaction
from django.utils import timezone

class ReservationTimeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationTime
        fields = ["lab_no", "date", "time", "status"]
        read_only_fields = ["status"]
    lab_no = serializers.CharField(required=True, max_length=20, write_only=True)

    def validate_date(self, value):
        today = timezone.localdate()
        if value <= today:
            raise serializers.ValidationError({"Error": "预约时间必须从明天开始"})
        return value

    def validate(self, attrs):
        lab_no = attrs.get("lab_no")
        try:
            lab = Laboratory.objects.get(lab_no = lab_no, is_deleted=False)
        except Laboratory.DoesNotExist:
            raise serializers.ValidationError({"Error": "该实验室不存在或者已停用"})

        if lab.status == Laboratory.StatusChoices.CLOSED:
            raise serializers.ValidationError({"Error": "该实验室已关闭"})

        if lab.status == Laboratory.StatusChoices.MAINTENANCE:
            raise serializers.ValidationError({"Error": "该实验室在维修中"})

        if lab.status != Laboratory.StatusChoices.OPEN:
            raise serializers.ValidationError({"Error": "该实验室当前不可使用"})

        date = attrs.get("date")
        time = attrs.get("time")

        reservationtime = ReservationTime.objects.filter(lab=lab, date=date, time=time)
        if reservationtime.exists():
            raise serializers.ValidationError({"Error": "该实验室的时间段已添加，不可重复添加"})
        
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lab_no = validated_data.pop("lab_no")
        lab = Laboratory.objects.get(lab_no = lab_no, is_deleted=False,
                                     status=Laboratory.StatusChoices.OPEN)
        return ReservationTime.objects.create(lab=lab, **validated_data)

class ReservationTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationTime
        fields = ["id", "lab", "date", "time", "status"]
        read_only_fields = ["id", "status"]

        
        

        