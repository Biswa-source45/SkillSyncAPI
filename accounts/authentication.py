from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model

User = get_user_model()

class CookieJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get('access_token')

        if not access_token:
            return None

        try:
            validated_token = AccessToken(access_token)
            user_id = validated_token['user_id']
            user = User.objects.get(id=user_id)
            return (user, None)
        except Exception as e:
            raise exceptions.AuthenticationFailed('Invalid or expired token.')
