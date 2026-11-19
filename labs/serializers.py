from labs.models import Laboratory
from lab_admins.models import LabAdmin
from rest_framework import serializers
from django.db import transaction

class LaboratoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratory
        fields = ["lab_no", "position", "labadmin_admin_no", "status"]

    labadmin_admin_no = serializers.CharField(required=True, write_only=True, max_length=20)

    def validate_lab_no(self, value):
        exists = Laboratory.objects.filter(lab_no = value).exists()
        if exists:
            raise serializers.ValidationError({"Error": "该实验室编号已存在"})
        return value

    def validate_labadmin_admin_no(self, value):
        exists = LabAdmin.objects.filter(is_deleted=False, user__is_deleted=False, 
                                         user__is_active=True, admin_no=value).exists()
        if not exists:
            raise serializers.ValidationError({"Error": "该管理员不存在或不可用"})
        return value

    @transaction.atomic
    def create(self, validated_data):
        labadmin_admin_no = validated_data.pop("labadmin_admin_no")
        labadmin = LabAdmin.objects.get(admin_no = labadmin_admin_no, is_deleted=False, 
                                        user__is_deleted=False, user__is_active=True)
        return Laboratory.objects.create(labadmin = labadmin, **validated_data)


class LaboratorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratory
        fields = ["id", "lab_no", "position", "labadmin", "status"]
        read_only_fields = ["id", "lab_no"]

    
        