from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password", "email", "phone"]

    username = serializers.CharField(required=True, max_length=150)
    password = serializers.CharField(required=True, min_length=8, write_only=True, trim_whitespace=False)

    def validate_username(self, value):
        exists = User.objects.filter(username=value).exists()
        if exists:
            raise serializers.ValidationError({"Error": "用户名已存在"})
        return value

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
        read_only_fields = ["id", "username"]
        

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "phone"]
        read_only_fields = ["id", "username"]


class UserLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(max_length=500, required=True, write_only=True)

    def validate(self, attrs):
        refresh = attrs.get("refresh")
        request = self.context["request"]

        try:
            token = RefreshToken(refresh)
            token_user_id = token[api_settings.USER_ID_CLAIM]
            if str(token_user_id) != str(request.user.pk):
                raise serializers.ValidationError({"Error": "不能注销其他用户的Token"})

            token.blacklist()

        except TokenError:
            raise serializers.ValidationError({"Error": "Refresh Token 已无效"})

        return attrs
    

