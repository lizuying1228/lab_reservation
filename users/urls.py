from django.urls import path
from users.views import UserRegisterView, UserLoginView, UserTokenRefreshView, UserLogoutView, UserProfileView

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('token/refresh/', UserTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('me/', UserProfileView.as_view(), name='profile')
]