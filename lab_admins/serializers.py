from lab_admins.models import LabAdmin
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction

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

    def validate(self, attrs):
        username = attrs.get("username")

        exists = User.objects.filter(username=username).exists()
        if exists:
            raise serializers.ValidationError({"username": "该用户已存在"})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop("username")
        password = validated_data.pop("password")
        user = User.objects.create_user(username = username, password = password)
        return LabAdmin.objects.create(user=user, **validated_data)


class LabAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabAdmin
        fields = ["id", "name", "admin_no", "birth_date", "user"]
        read_only_fields = ["id", "admin_no", "user"]
        