from django.urls import path
from .views import (
    RegisterView, LoginView, ProfileView, FollowUserView, UnfollowUserView,
    UserListView, UserDetailView, CookieTokenRefreshView, LogoutView, MyLikedPostsView, UserPostsView, RequestPasswordResetView, VerifyOTPView, ResetPasswordView, 
)
from .views import imagekit_auth_view


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('follow/<int:user_id>/', FollowUserView.as_view(), name='follow'),
    path('unfollow/<int:user_id>/', UnfollowUserView.as_view(), name='unfollow'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:id>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/posts/', UserPostsView.as_view(), name='user-posts'),
    path('refresh/', CookieTokenRefreshView.as_view(), name='token-refresh'),
    path('liked-posts/', MyLikedPostsView.as_view(), name='my-liked-posts'),
    path('forgot-password/', RequestPasswordResetView.as_view(), name='forgot-password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path("imagekit-auth/", imagekit_auth_view, name="imagekit-auth"),

]
