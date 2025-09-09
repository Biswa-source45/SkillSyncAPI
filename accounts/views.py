from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth import authenticate
from django.conf import settings
from .models import User
from .serializers import RequestPasswordResetSerializer, ResetPasswordSerializer, UserSerializer, RegisterSerializer, ProfileSerializer, LoginSerializer, VerifyOTPSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.exceptions import ValidationError
from posts.serializers import PostSerializer
from posts.models import Post
from django.core.mail import send_mail
from .models import PasswordResetOTP
import random
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from imagekitio import ImageKit
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])  # remove if public
def imagekit_auth_view(request):
    imagekit = ImageKit(
        public_key=settings.IMAGEKIT_PUBLIC_KEY,
        private_key=settings.IMAGEKIT_PRIVATE_KEY,
        url_endpoint=settings.IMAGEKIT_URL_ENDPOINT,
    )
    auth_params = imagekit.get_authentication_parameters()
    return Response(auth_params)

# Utility function to set cookies
def set_jwt_cookies(response, refresh, access):
    response.set_cookie(
        key='access_token', value=str(access),
        httponly=True, secure=False, samesite='Lax',
        max_age=60*60*24
    )
    response.set_cookie(
        key='refresh_token', value=str(refresh),
        httponly=True, secure=False, samesite='Lax',
        max_age=60*60*24*7
    )
    return response


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        resp = Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return set_jwt_cookies(resp, refresh, access)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response({
            'message': 'Login successful',
            'access': access_token,
            'refresh': refresh_token,
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,
            samesite='None',
            max_age=60 * 60 * 24
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite='None',
            max_age=60 * 60 * 24 * 7
        )

        return response


class CookieTokenRefreshView(APIView):
    """
    Refresh access token using refresh token stored in cookies.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ✅ Pass refresh token into serializer safely
        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Serializer gives us {"access": "..."} (and optionally "refresh" if rotation enabled)
        data = serializer.validated_data
        access = data.get("access")

        # ✅ Return new access token + also set it as cookie (like your LoginView does)
        resp = Response({"access": access}, status=status.HTTP_200_OK)
        resp.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=False,  # set True in production with HTTPS
            samesite="Lax",
            max_age=60 * 60 * 24,  # 1 day
        )

        # If you want rotated refresh tokens, handle here:
        new_refresh = data.get("refresh")
        if new_refresh:
            resp.set_cookie(
                key="refresh_token",
                value=new_refresh,
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=60 * 60 * 24 * 7,  # 7 days
            )

        return resp


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                raise ValidationError({'error': 'Invalid or expired refresh token.'})

        response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class FollowUserView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        user_to_follow = User.objects.get(id=user_id)
        request.user.following.add(user_to_follow)
        return Response({'message': 'Followed Successfully'})


class UnfollowUserView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        user_to_unfollow = User.objects.get(id=user_id)
        request.user.following.remove(user_to_unfollow)
        return Response({'message': 'Unfollowed Successfully'})


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'
    permission_classes = [permissions.AllowAny]
    
class UserPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.AllowAny]  # Publicly accessible

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Post.objects.filter(author__id=user_id)

class MyLikedPostsView(generics.ListAPIView):
    """
    Returns posts liked by the current authenticated user.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Post.objects.filter(likes=user)
    


def generate_otp():
    return str(random.randint(100000, 999999))


class RequestPasswordResetView(generics.GenericAPIView):
    serializer_class = RequestPasswordResetSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            otp = generate_otp()
            PasswordResetOTP.objects.create(user=user, otp=otp)

            html_message = render_to_string('accounts/otp_email_template.html', {
                'username': user.username,
                'email': user.email,
                'otp': otp,
            })

            email_message = EmailMessage(
                subject='SkillSync Password Reset OTP',
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email],
            )
            email_message.content_subtype = 'html'
            email_message.send()

            return Response({'message': 'OTP sent to your email'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'Email does not exist'}, status=status.HTTP_404_NOT_FOUND)

class VerifyOTPView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)
            otp_record = PasswordResetOTP.objects.filter(user=user, otp=otp).last()

            if not otp_record or otp_record.is_expired():
                return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'message': 'OTP verified successfully'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            PasswordResetOTP.objects.filter(user=user).delete()  # Clear any existing OTPs

            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)