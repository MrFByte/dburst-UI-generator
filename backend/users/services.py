from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def issue_auth_cookies(response, user):
    """Mints a JWT pair for `user` and attaches them as httponly cookies on `response`.

    Shared by every login path (Google, GitHub, email OTP) so they all produce
    the exact same session shape.
    """
    refresh = RefreshToken.for_user(user)

    response.set_cookie(
        key="refresh",
        value=str(refresh),
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRY,
    )
    response.set_cookie(
        key="access",
        value=str(refresh.access_token),
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRY,
    )
    return response
