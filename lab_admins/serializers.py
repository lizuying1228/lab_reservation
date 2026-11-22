from lab_admins.models import LabAdmin
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction
from lab_admins.services import create_labadmin, update_labadmin

User = get_user_model()
class LabAdminCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabAdmin
        fields = ["name", "admin_no", "birth_date", "username", "password"]

    username = serializers.CharField(max_length=150, required=True, write_only=True)
    password = serializers.CharField(min_length=8, write_only=True, required=True, trim_whitespace=False)

    def validate_admin_no(self, value):
        exists = LabAdmin.objects.filter(admin_no = value).exists()
        if exists:
            raise serializers.ValidationError({"Error": "实验室管理员编号已存在"})
        return value

    def update(self, instance, validated_data):
        operator_id = self.context["request"].user.id
        return update_labadmin(labadmin_id=instance.id, validated_data=validated_data, operator_id=operator_id)

    def create(self, validated_data):
        operator_id = self.context["request"].user.id
        return create_labadmin(validated_data=validated_data, operator_id=operator_id)

class LabAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabAdmin
        fields = ["id", "name", "admin_no", "birth_date", "user"]
        read_only_fields = ["id", "admin_no", "user"]
        