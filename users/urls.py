from django.urls import path
from users.views import (UserRegisterView, UserLoginView, UserTokenRefreshView, 
                         UserLogoutView, UserProfileView, UserDeleteView, UserView)

urlpatterns = [
    path('register/', UserRegisterView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('token/refresh/', UserTokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('me/', UserProfileView.as_view(), name='profile'),
    path('<int:user_id>/', UserDeleteView.as_view(), name='user-delete'),
    path('', UserView.as_view(), name='user')
]