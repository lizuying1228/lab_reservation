from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.contrib.auth import get_user_model
from users.serializers import (
    UserRegisterSerializer, 
    UserLogoutSerializer, 
    UserProfileSerializer, 
    UserSerializer,
    UserRegisterResponseSerializer,
    UserProfileResponseSerializer,
    UserProfileUpdateResponseSerializer,
    MessageResponseSerializer,
    ManualValidationErrorResponseSerializer,
    )
from rest_framework import status
from users.services import delete_user
from users.permissions import IsSuperuser
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import serializers
from drf_spectacular.utils import extend_schema
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Create your views here.
class UserRegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=UserRegisterSerializer,
        responses={
            201: UserRegisterResponseSerializer,
            400: ManualValidationErrorResponseSerializer
        }
    )
    def post(self, request):
        data = request.data
        serializer = UserRegisterSerializer(data=data)

        if serializer.is_valid():
            user = serializer.save()
            logger.info("User registered successfully: user_id=%s", user.pk)
            return Response({"message": "注册成功", 
                             "user": serializer.data}, status=status.HTTP_201_CREATED)
        
        logger.warning("User registration validation failed: errors=%s", serializer.errors)
        return Response({"Error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(TokenObtainPairView):
    pass

class UserTokenRefreshView(TokenRefreshView):
    pass

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=UserLogoutSerializer,
        responses={
            200: MessageResponseSerializer,
            400: ManualValidationErrorResponseSerializer
        }
    )
    def post(self, request):
        data = request.data
        serializer = UserLogoutSerializer(data=data, context={"request": request})

        if serializer.is_valid():
            logger.info("User logout successfully: user_id=%s", request.user.pk)
            return Response({"message": "登出成功"}, status=status.HTTP_200_OK)

        logger.warning("User logout validation failed: user_id=%s", request.user.pk)
        return Response({"Error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileResponseSerializer}
    )
    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        logger.info("User get profile successfully: user_id=%s", user.pk)
        return Response({"user": serializer.data}, status=status.HTTP_200_OK)

    @extend_schema(
        request=UserProfileSerializer,
        responses={
            200: UserProfileResponseSerializer,
            400: ManualValidationErrorResponseSerializer
        }
    )
    def patch(self, request):
        user = request.user
        serializer = UserProfileSerializer(instance=user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info("User update successfully: user_id=%s", user.pk)
            return Response({"message": "修改成功",
                             "user": serializer.data}, status=status.HTTP_200_OK)

        logger.warning("User update validation failed: user_id=%s", user.pk)
        return Response({"Error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserDeleteView(APIView):
    permission_classes = [IsSuperuser]

    @extend_schema(
        responses={
            204: None
        }
    )
    def delete(self, request, user_id):
        delete_user(target_user_id=user_id, operator_id=request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserView(ListAPIView):
    permission_classes = [IsSuperuser]
    serializer_class = UserSerializer
    filterset_fields = ["username", "is_active", "is_superuser"]
    search_fields = ["username", "email", "phone"]
    ordering_fields = ["id", "username"]
    ordering = ["id"]

    def get_queryset(self):
        return User.objects.filter(is_deleted=False, is_active=True)
