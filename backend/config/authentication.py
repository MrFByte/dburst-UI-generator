from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads the access token from cookies
    instead of the Authorization header.
    """
    def authenticate(self, request):
        raw_token = request.COOKIES.get('access')
        
        if not raw_token:
            header = self.get_header(request)
            if header is None:
                return None
            raw_token = self.get_raw_token(header)
        
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken as e:
            raise AuthenticationFailed(f'Invalid token: {str(e)}')
