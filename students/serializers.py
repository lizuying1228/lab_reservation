from students.models import Student
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()
class StudentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["name", "student_no", "birth_date", "user_id", "username", "password"]

    user_id = serializers.IntegerField(required=False, min_value=1, write_only=True)
    username = serializers.CharField(max_length=150, required=False, write_only=True)
    password = serializers.CharField(required=False, min_length=8, write_only=True, trim_whitespace=False)

    def validate_student_no(self, value):
        exists = Student.objects.filter(student_no = value).exists()
        if exists:
            raise serializers.ValidationError({"student_no": "学号不能重复"})
        return value

    def validate(self, attrs):
        user_id = attrs.get("user_id", "")
        username = attrs.get("username", "")
        password = attrs.get("password", "")

        if user_id:
            try:
                target_user = User.objects.get(id = user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError({"Error": "该用户不存在"})

            if not target_user.is_active or target_user.is_deleted:
                raise serializers.ValidationError({"Error": "该用户已停用"})

            if hasattr(target_user, "labadmin"):
                raise serializers.ValidationError({"Error": "该用户已绑定实验室管理员"})

            if target_user.is_superuser:
                raise serializers.ValidationError({"Error": "该用户已绑定超级管理员"})

            if hasattr(target_user, "student"):
                raise serializers.ValidationError({"Error": "该用户已绑定学生档案"})

            if username:
                raise serializers.ValidationError({"Error": "已有未绑定用户，不需要重新注册用户"})

            if password:
                raise serializers.ValidationError({"Error": "已有未绑定用户，不需要重新注册用户"})
        else:
            if not username:
                raise serializers.ValidationError({"username": "必须有用户名"})
            
            if not password or len(password) < 8:
                raise serializers.ValidationError({"password": "必须有密码，且不小于八位数"})

            exists = User.objects.filter(username = username).exists()
            if exists:
                raise serializers.ValidationError({"username": "用户名重复"})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user_id = validated_data.pop("user_id", None)

        if user_id:
            user = User.objects.get(id = user_id)
        else:
            username = validated_data.pop("username")
            password = validated_data.pop("password")
            user = User.objects.create_user(username=username, password=password)

        return Student.objects.create(user = user, **validated_data)

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id", "name", "student_no", "birth_date", "user"]
        read_only_fields = ["student_no", "user", "id"]
