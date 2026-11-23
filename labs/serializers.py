from labs.models import Laboratory
from lab_admins.models import LabAdmin
from rest_framework import serializers
from labs.services import create_laboratory, update_laboratory, delete_laboratory

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

    def create(self, validated_data):
        operator_id = self.context["request"].user.id
        laboratory = create_laboratory(validated_data=validated_data, operator_id=operator_id)
        return laboratory


class LaboratorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Laboratory
        fields = ["id", "lab_no", "position", "labadmin", "status"]
        read_only_fields = ["id", "lab_no"]

    def update(self, instance, validated_data):
        operator_id = self.context["request"].user.id
        laboratory = update_laboratory(lab_id=instance.id, validated_data=validated_data, operator_id=operator_id)
        return laboratory