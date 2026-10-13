"""
End-to-end checks of the cookie-only session contract (see Plan/auth-audit.md):
cookie attributes, CSRF, refresh rotation, logout revocation, and that
protected resources answer 401 / deny cross-user access.
"""
from unittest.mock import patch

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from generation.models import Generations
from otp_auth.services import generate_otp
from projects.models import Project
from users.models import User

from .conftest import fetch_csrf, login_with_cookies

ACCESS = settings.AUTH_ACCESS_COOKIE
REFRESH = settings.AUTH_REFRESH_COOKIE


def otp_login(client, email="flow@example.com"):
    token = fetch_csrf(client)
    code = generate_otp(email)
    res = client.post(
        reverse("otp-verify"), {"email": email, "code": code},
        format="json", HTTP_X_CSRFTOKEN=token,
    )
    assert res.status_code == 200, res.data
    return res, token


# --------------------------------------------------------------------------
# Cookie attributes
# --------------------------------------------------------------------------

@pytest.mark.django_db
def test_login_sets_hardened_cookies(csrf_client):
    res, _ = otp_login(csrf_client)

    access, refresh = res.cookies[ACCESS], res.cookies[REFRESH]
    for cookie in (access, refresh):
        assert cookie["httponly"] is True
        assert cookie["secure"] is True
        assert cookie["samesite"] == "Lax"

    assert access["path"] == "/"
    assert refresh["path"] == settings.AUTH_REFRESH_COOKIE_PATH
    assert int(access["max-age"]) == settings.ACCESS_TOKEN_EXPIRY == 900
    assert int(refresh["max-age"]) == settings.REFRESH_TOKEN_EXPIRY

    # No token ever appears in a response body.
    assert "access" not in res.data and "refresh" not in res.data


@pytest.mark.django_db
def test_csrf_endpoint_issues_readable_cookie(csrf_client):
    res = csrf_client.get(reverse("csrf-token"))
    assert res.status_code == 200
    cookie = res.cookies["csrftoken"]
    assert cookie.value
    assert not cookie["httponly"]  # the SPA must read it to echo it back


# --------------------------------------------------------------------------
# Authentication: cookie only, generic errors, 401s
# --------------------------------------------------------------------------

@pytest.mark.django_db
def test_profile_with_access_cookie(csrf_client, user):
    login_with_cookies(csrf_client, user)
    res = csrf_client.get(reverse("user-profile"))
    assert res.status_code == 200
    assert res.data["user"]["email"] == user.email


@pytest.mark.django_db
def test_profile_without_cookie_is_401(csrf_client):
    assert csrf_client.get(reverse("user-profile")).status_code == 401


@pytest.mark.django_db
def test_bearer_header_is_ignored(csrf_client, user):
    access = RefreshToken.for_user(user).access_token
    res = csrf_client.get(reverse("user-profile"), HTTP_AUTHORIZATION=f"Bearer {access}")
    assert res.status_code == 401


@pytest.mark.django_db
def test_refresh_token_in_access_cookie_is_rejected(csrf_client, user):
    csrf_client.cookies[ACCESS] = str(RefreshToken.for_user(user))
    assert csrf_client.get(reverse("user-profile")).status_code == 401


@pytest.mark.django_db
def test_invalid_token_error_is_generic(csrf_client):
    csrf_client.cookies[ACCESS] = "not-a-jwt"
    res = csrf_client.get(reverse("user-profile"))
    assert res.status_code == 401
    assert str(res.data["detail"]) == "Invalid or expired session."


@pytest.mark.django_db
@pytest.mark.parametrize("url_name,kwargs", [
    ("user-profile", {}),
    ("recent-projects", {}),
    ("all-projects", {}),
    ("available-models", {}),
    ("clear-user-sessions", {}),
])
def test_protected_endpoints_require_login(csrf_client, url_name, kwargs):
    url = reverse(url_name, kwargs=kwargs)
    res = csrf_client.post(url) if url_name == "clear-user-sessions" else csrf_client.get(url)
    assert res.status_code == 401


# --------------------------------------------------------------------------
# CSRF
# --------------------------------------------------------------------------

@pytest.mark.django_db
def test_cookie_authenticated_post_without_csrf_is_rejected(csrf_client, user):
    login_with_cookies(csrf_client, user)
    res = csrf_client.post(reverse("create-project"), {"title": "x"}, format="json")
    assert res.status_code == 403
    assert "CSRF" in str(res.data["detail"])
    assert not Project.objects.exists()


@pytest.mark.django_db
def test_cookie_authenticated_post_with_csrf_succeeds(csrf_client, user):
    token = fetch_csrf(csrf_client)
    login_with_cookies(csrf_client, user)
    res = csrf_client.post(
        reverse("create-project"), {"title": "x"}, format="json", HTTP_X_CSRFTOKEN=token
    )
    assert res.status_code == 201


@pytest.mark.django_db
def test_wrong_csrf_token_is_rejected(csrf_client, user):
    fetch_csrf(csrf_client)
    login_with_cookies(csrf_client, user)
    res = csrf_client.post(
        reverse("create-project"), {"title": "x"}, format="json", HTTP_X_CSRFTOKEN="x" * 32
    )
    assert res.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["otp-request", "otp-verify", "token-refresh", "logout", "oauth-start", "google-auth"])
def test_unauthenticated_auth_endpoints_require_csrf(csrf_client, url_name):
    """Login CSRF: a cross-site form must not be able to drive these."""
    res = csrf_client.post(reverse(url_name), {}, format="json")
    assert res.status_code == 403


@pytest.mark.django_db
def test_untrusted_origin_is_rejected(csrf_client, user):
    token = fetch_csrf(csrf_client)
    login_with_cookies(csrf_client, user)
    res = csrf_client.post(
        reverse("create-project"), {"title": "x"}, format="json",
        HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN="https://evil.example",
    )
    assert res.status_code == 403


# --------------------------------------------------------------------------
# Refresh rotation
# --------------------------------------------------------------------------

@pytest.mark.django_db
def test_refresh_rotates_and_blacklists_old_token(csrf_client, user):
    token = fetch_csrf(csrf_client)
    old_refresh = str(login_with_cookies(csrf_client, user))

    res = csrf_client.post(reverse("token-refresh"), HTTP_X_CSRFTOKEN=token)
    assert res.status_code == 200
    assert "access" not in res.data and "refresh" not in res.data

    new_refresh = res.cookies[REFRESH].value
    assert new_refresh and new_refresh != old_refresh
    assert res.cookies[REFRESH]["path"] == settings.AUTH_REFRESH_COOKIE_PATH
    assert res.cookies[ACCESS]["httponly"] is True

    # The new access cookie authenticates.
    assert csrf_client.get(reverse("user-profile")).status_code == 200

    # Replaying the old refresh token fails and clears cookies.
    csrf_client.cookies[REFRESH] = old_refresh
    replay = csrf_client.post(reverse("token-refresh"), HTTP_X_CSRFTOKEN=token)
    assert replay.status_code == 401
    assert replay.cookies[REFRESH].value == ""
    assert replay.cookies[ACCESS].value == ""


@pytest.mark.django_db
def test_refresh_without_cookie_is_401(csrf_client):
    token = fetch_csrf(csrf_client)
    res = csrf_client.post(reverse("token-refresh"), HTTP_X_CSRFTOKEN=token)
    assert res.status_code == 401


@pytest.mark.django_db
def test_refresh_for_inactive_user_is_401(csrf_client, user):
    token = fetch_csrf(csrf_client)
    login_with_cookies(csrf_client, user)
    user.is_active = False
    user.save()
    res = csrf_client.post(reverse("token-refresh"), HTTP_X_CSRFTOKEN=token)
    assert res.status_code == 401


# --------------------------------------------------------------------------
# Logout
# --------------------------------------------------------------------------

@pytest.mark.django_db
def test_logout_blacklists_and_invalidates(csrf_client, user):
    token = fetch_csrf(csrf_client)
    refresh = login_with_cookies(csrf_client, user)
    access_value = str(csrf_client.cookies[ACCESS].value)
    refresh_value = str(refresh)

    res = csrf_client.post(reverse("logout"), HTTP_X_CSRFTOKEN=token)
    assert res.status_code == 200

    # Deleted with the same attributes they were set with.
    assert res.cookies[ACCESS].value == "" and res.cookies[ACCESS]["path"] == "/"
    assert res.cookies[REFRESH].value == ""
    assert res.cookies[REFRESH]["path"] == settings.AUTH_REFRESH_COOKIE_PATH
    assert res.cookies[REFRESH]["samesite"] == "Lax"
    assert res.cookies[REFRESH]["max-age"] == 0

    assert BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()

    # Browser has no cookies now -> 401.
    assert csrf_client.get(reverse("user-profile")).status_code == 401

    # A copied access cookie is revoked too, not just deleted.
    csrf_client.cookies[ACCESS] = access_value
    assert csrf_client.get(reverse("user-profile")).status_code == 401

    # And the refresh token can't mint a new session.
    csrf_client.cookies[REFRESH] = refresh_value
    assert csrf_client.post(reverse("token-refresh"), HTTP_X_CSRFTOKEN=token).status_code == 401


@pytest.mark.django_db
def test_logout_without_session_still_clears_cookies(csrf_client):
    token = fetch_csrf(csrf_client)
    res = csrf_client.post(reverse("logout"), HTTP_X_CSRFTOKEN=token)
    assert res.status_code == 200
    assert res.cookies[ACCESS].value == ""


@pytest.mark.django_db
def test_clear_sessions_only_affects_requesting_user(csrf_client, user):
    other = User.objects.create_user(email="other@example.com")
    other_refresh = RefreshToken.for_user(other)
    RefreshToken.for_user(user)  # another device

    token = fetch_csrf(csrf_client)
    login_with_cookies(csrf_client, user)
    res = csrf_client.post(reverse("clear-user-sessions"), HTTP_X_CSRFTOKEN=token)

    assert res.status_code == 200
    assert res.data["sessions_cleared"] == 2
    assert not OutstandingToken.objects.filter(user=user, blacklistedtoken__isnull=True).exists()
    assert not BlacklistedToken.objects.filter(token__jti=other_refresh["jti"]).exists()
    assert csrf_client.get(reverse("user-profile")).status_code == 401


# --------------------------------------------------------------------------
# Admin-only and throttling
# --------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("url_name", ["session-analytics", "cache-stats"])
def test_admin_endpoints_deny_regular_users(csrf_client, user, url_name):
    assert csrf_client.get(reverse(url_name)).status_code == 401
    login_with_cookies(csrf_client, user)
    assert csrf_client.get(reverse(url_name)).status_code == 403


@pytest.mark.django_db
@patch("otp_auth.views.send_otp_email")
def test_otp_request_is_throttled_per_client(mock_send, csrf_client, settings):
    settings.OTP_MAX_REQUESTS_PER_WINDOW = 100  # isolate the IP throttle
    token = fetch_csrf(csrf_client)
    statuses = [
        csrf_client.post(
            reverse("otp-request"), {"email": f"u{i}@example.com"},
            format="json", HTTP_X_CSRFTOKEN=token,
        ).status_code
        for i in range(7)
    ]
    assert statuses[:5] == [200] * 5
    assert statuses[-1] == 429


# --------------------------------------------------------------------------
# IDOR: another user's resources are never reachable
# --------------------------------------------------------------------------

@pytest.fixture
def victim_generation(db):
    victim = User.objects.create_user(email="victim@example.com")
    project = Project.objects.create(user=victim, title="secret")
    generation = Generations.objects.create(
        project=project, prompt="p", schema={"type": "Page"}, llm_provider="groq", status="success"
    )
    return project, generation


@pytest.mark.django_db
def test_idor_denied_on_other_users_resources(csrf_client, user, victim_generation):
    project, generation = victim_generation
    token = fetch_csrf(csrf_client)
    login_with_cookies(csrf_client, user)

    assert csrf_client.get(reverse("project-detail", args=[project.id])).status_code == 404
    assert csrf_client.get(reverse("generation-detail", args=[generation.id])).status_code == 404
    assert csrf_client.get(reverse("chat-history", args=[generation.id])).status_code == 404
    assert csrf_client.get(reverse("get-schema", args=[generation.id])).status_code == 403
    assert csrf_client.get(reverse("list-patches", args=[generation.id])).status_code == 403

    res = csrf_client.post(
        reverse("refine-ui"), {"generation_id": str(generation.id), "message": "hi"},
        format="json", HTTP_X_CSRFTOKEN=token,
    )
    assert res.status_code == 404

    res = csrf_client.delete(reverse("clear-cache", args=[generation.id]), HTTP_X_CSRFTOKEN=token)
    assert res.status_code == 403

    listed = csrf_client.get(reverse("all-projects")).data["results"]
    assert all(p["id"] != str(project.id) for p in listed)
