from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken

from config.authentication import REVOKED_ACCESS_CACHE_PREFIX

# Cookie names used before the cookie rename — still present in browsers that
# logged in before this deploy. Cleared on login/logout so they can't linger.
LEGACY_COOKIE_NAMES = ("access", "refresh")


def _cookie_kwargs(path):
    return {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
        "path": path,
    }


def set_auth_cookies(response, access, refresh):
    """Attaches an access/refresh pair as httponly cookies.

    The refresh cookie is path-scoped to /users/auth/ so it only travels to
    the refresh/logout endpoints, never with ordinary API calls.
    """
    response.set_cookie(
        settings.AUTH_ACCESS_COOKIE,
        str(access),
        max_age=settings.ACCESS_TOKEN_EXPIRY,
        **_cookie_kwargs(settings.AUTH_COOKIE_PATH),
    )
    response.set_cookie(
        settings.AUTH_REFRESH_COOKIE,
        str(refresh),
        max_age=settings.REFRESH_TOKEN_EXPIRY,
        **_cookie_kwargs(settings.AUTH_REFRESH_COOKIE_PATH),
    )
    _delete_legacy_cookies(response)
    return response


def clear_auth_cookies(response):
    """Deletes the auth cookies with the same path/samesite/secure they were set
    with — a deletion with different attributes is a different cookie and the
    browser keeps the original."""
    response.delete_cookie(
        settings.AUTH_ACCESS_COOKIE,
        path=settings.AUTH_COOKIE_PATH,
        samesite=settings.COOKIE_SAMESITE,
    )
    response.delete_cookie(
        settings.AUTH_REFRESH_COOKIE,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        samesite=settings.COOKIE_SAMESITE,
    )
    _delete_legacy_cookies(response)
    return response


def _delete_legacy_cookies(response):
    for name in LEGACY_COOKIE_NAMES:
        response.delete_cookie(name, path="/", samesite=settings.COOKIE_SAMESITE)


def issue_auth_cookies(response, user):
    """Mints a JWT pair for `user` and attaches them as httponly cookies on `response`.

    Shared by every login path (Google, GitHub, email OTP) so they all produce
    the exact same session shape.
    """
    refresh = RefreshToken.for_user(user)
    return set_auth_cookies(response, refresh.access_token, refresh)


def revoke_access_token(validated_token):
    """Rejects this access token's jti for the rest of its lifetime.

    Access tokens are stateless, so without this a copied access cookie keeps
    working after logout until it expires.
    """
    jti = validated_token.get("jti")
    exp = validated_token.get("exp")
    if not jti or not exp:
        return
    remaining = int(exp - datetime.now(dt_timezone.utc).timestamp())
    if remaining > 0:
        cache.set(f"{REVOKED_ACCESS_CACHE_PREFIX}{jti}", 1, timeout=remaining)
