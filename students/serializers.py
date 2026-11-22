from students.models import Student
from rest_framework import serializers
from django.contrib.auth import get_user_model
from students.services import create_student, update_student

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

        if user_id is not None:
            if username or password:
                raise serializers.ValidationError({"Error": "已有未绑定用户，不需要重新注册用户"})
        else:
            if not username or not password:
                raise serializers.ValidationError({"username": "必须有用户名和密码，密码不能小于八位数"})

        return attrs

    def create(self, validated_data):
        operator_id = self.context["request"].user.id
        return create_student(validated_data=validated_data, operator_id=operator_id)

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["id", "name", "student_no", "birth_date", "user"]
        read_only_fields = ["student_no", "user", "id"]

    def update(self, instance, validated_data):
        operator_id = self.context["request"].user.id
        return update_student(student_id=instance.id, validated_data=validated_data, operator_id=operator_id)
