from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password", "email", "phone"]

    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(required=True, min_length=8, write_only=True, trim_whitespace=False)

    # def validate_password(self, value):
    #     try:
    #         validate_password(value)
    #     except DjangoValidationError as exc:
    #         raise serializers.ValidationError(exc.messages)
    #     return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "phone"]
        read_only_fields = ["id"]