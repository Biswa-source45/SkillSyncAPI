from rest_framework import serializers
from .models import User
from .models import User, PasswordResetOTP
from django.contrib.auth import authenticate

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'error_messages': {'unique': "This email is already registered."}},
            'username': {'error_messages': {'unique': "This username is already taken."}},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    
class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = data.get('username_or_email')
        password = data.get('password')

        user = None

        if '@' in identifier:
            # User is trying to login with email
            try:
                user_obj = User.objects.get(email=identifier)
                user = authenticate(username=user_obj.username, password=password)
                if not user:
                    raise serializers.ValidationError("Invalid email or password")
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this email does not exist")
        else:
            # User is trying to login with username
            user = authenticate(username=identifier, password=password)
            if not user:
                raise serializers.ValidationError("Invalid username or password")

        data['user'] = user
        return data

class ProfileSerializer(serializers.ModelSerializer):
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'profile_photo', 'bio', 'gender', 'role',
            'interests', 'followers', 'following', 'full_name', 'is_following'
        ]
        read_only_fields = ['followers', 'following']

    def get_is_following(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user.following.filter(id=obj.id).exists()
        return False


class UserSerializer(serializers.ModelSerializer):
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'profile_photo', 'bio', 'full_name', 'is_following'
        ]

    def get_is_following(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return request.user.following.filter(id=obj.id).exists()
        return False



class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)