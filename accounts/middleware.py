import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from accounts.models import User

class RefreshTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')

        if access_token:
            try:
                payload = jwt.decode(
                    access_token, 
                    settings.SIMPLE_JWT['SIGNING_KEY'], 
                    algorithms=[settings.SIMPLE_JWT['ALGORITHM']]
                )
                # Token is valid, do nothing
            except jwt.ExpiredSignatureError:
                # Access token expired, try refreshing
                if refresh_token:
                    try:
                        refresh_payload = jwt.decode(
                            refresh_token, 
                            settings.SIMPLE_JWT['SIGNING_KEY'], 
                            algorithms=[settings.SIMPLE_JWT['ALGORITHM']]
                        )
                        user_id = refresh_payload.get('user_id')
                        user = User.objects.get(id=user_id)
                        new_refresh = RefreshToken.for_user(user)
                        request.new_access_token = str(new_refresh.access_token)

                    except jwt.ExpiredSignatureError:
                        # Refresh token expired, user must login again
                        pass
                    except Exception:
                        pass
            except Exception:
                pass

    def process_response(self, request, response):
        new_token = getattr(request, 'new_access_token', None)
        if new_token:
            response.set_cookie(
                key='access_token',
                value=new_token,
                httponly=True,
                secure=False,  # Set to True on production HTTPS
                samesite='Lax',
                max_age=60 * 60 * 24 # Optional: 5 mins expiry
            )
        return response


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        access_token = request.COOKIES.get('access_token')
        if access_token:
            try:
                token = AccessToken(access_token)
                user_id = token['user_id']
                request.user = SimpleLazyObject(lambda: User.objects.get(id=user_id))
                print(f'[Middleware] Authenticated User: {request.user.username}')
            except Exception as e:
                print('Token Error:', e)
        return self.get_response(request)