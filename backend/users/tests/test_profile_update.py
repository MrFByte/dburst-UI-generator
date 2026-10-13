import pytest
from django.urls import reverse

from users.models import User

from .conftest import fetch_csrf, login_with_cookies


@pytest.fixture
def url():
    return reverse("user-profile")


@pytest.fixture
def logged_in(csrf_client, user):
    """(client, csrf_token) for `user`, authenticated via real cookies."""
    token = fetch_csrf(csrf_client)
    login_with_cookies(csrf_client, user)
    return csrf_client, token


def patch(client, url, token, data):
    return client.patch(url, data, format="json", HTTP_X_CSRFTOKEN=token)


@pytest.mark.django_db
def test_update_name_and_avatar(logged_in, url, user):
    client, token = logged_in
    res = patch(client, url, token, {"name": "  New Name  ", "avatar_url": "https://cdn.example.com/a.png"})

    assert res.status_code == 200
    assert res.data["user"]["name"] == "New Name"
    assert res.data["user"]["avatar_url"] == "https://cdn.example.com/a.png"
    assert set(res.data["user"]) == {"id", "email", "name", "avatar_url", "role"}
    user.refresh_from_db()
    assert user.name == "New Name"
    assert user.avatar_url == "https://cdn.example.com/a.png"


@pytest.mark.django_db
def test_partial_update_keeps_other_field(logged_in, url, user):
    user.avatar_url = "https://cdn.example.com/a.png"
    user.save()
    client, token = logged_in
    res = patch(client, url, token, {"name": "Only Name"})
    assert res.status_code == 200
    assert res.data["user"]["avatar_url"] == "https://cdn.example.com/a.png"


@pytest.mark.django_db
@pytest.mark.parametrize("cleared", ["", None, "   "])
def test_clear_avatar(logged_in, url, user, cleared):
    user.avatar_url = "https://cdn.example.com/a.png"
    user.save()
    client, token = logged_in
    res = patch(client, url, token, {"avatar_url": cleared})
    assert res.status_code == 200
    assert res.data["user"]["avatar_url"] is None
    user.refresh_from_db()
    assert user.avatar_url is None


@pytest.mark.django_db
def test_unauthenticated_is_401(csrf_client, url):
    token = fetch_csrf(csrf_client)
    res = patch(csrf_client, url, token, {"name": "x"})
    assert res.status_code == 401


@pytest.mark.django_db
def test_missing_csrf_is_rejected(csrf_client, url, user):
    login_with_cookies(csrf_client, user)
    res = csrf_client.patch(url, {"name": "Hacked"}, format="json")
    assert res.status_code == 403
    user.refresh_from_db()
    assert user.name == "Test User"


@pytest.mark.django_db
def test_put_not_allowed(logged_in, url):
    client, token = logged_in
    res = client.put(url, {"name": "x"}, format="json", HTTP_X_CSRFTOKEN=token)
    assert res.status_code == 405


@pytest.mark.django_db
@pytest.mark.parametrize("bad_url", [
    "javascript:alert(1)",
    "data:image/png;base64,AAAA",
    "file:///etc/passwd",
    "ftp://example.com/a.png",
    "//example.com/a.png",
    "/relative/path.png",
    "not a url",
    "https://user:pass@example.com/a.png",
    "https://user@example.com/a.png",
    "http://localhost/a.png",
    "http://foo.localhost/a.png",
    "http://127.0.0.1/a.png",
    "http://10.0.0.5/a.png",
    "http://192.168.1.1/a.png",
    "http://169.254.169.254/latest/meta-data",
    "http://[::1]/a.png",
    "https://example.com/" + "a" * 2048,
])
def test_bad_avatar_url_rejected(logged_in, url, user, bad_url):
    client, token = logged_in
    res = patch(client, url, token, {"avatar_url": bad_url})
    assert res.status_code == 400
    assert "avatar_url" in res.data and isinstance(res.data["avatar_url"], list)
    user.refresh_from_db()
    assert user.avatar_url is None


@pytest.mark.django_db
@pytest.mark.parametrize("bad_name", ["", "   ", "\n\t", "a" * 121, "<b>x</b>", "<script>alert(1)</script>"])
def test_bad_name_rejected(logged_in, url, user, bad_name):
    client, token = logged_in
    res = patch(client, url, token, {"name": bad_name})
    assert res.status_code == 400
    assert "name" in res.data
    user.refresh_from_db()
    assert user.name == "Test User"


@pytest.mark.django_db
def test_name_strips_control_characters(logged_in, url):
    client, token = logged_in
    res = patch(client, url, token, {"name": "Ada\u0007 Love\u202elace\n"})
    assert res.status_code == 200
    assert res.data["user"]["name"] == "Ada Lovelace"


@pytest.mark.django_db
def test_name_with_nul_byte_rejected(logged_in, url):
    """DRF's CharField refuses NUL outright (before our stripping runs)."""
    client, token = logged_in
    res = patch(client, url, token, {"name": "Ada\u0000"})
    assert res.status_code == 400
    assert "name" in res.data


@pytest.mark.django_db
def test_name_max_length_accepted(logged_in, url):
    client, token = logged_in
    res = patch(client, url, token, {"name": "a" * 120})
    assert res.status_code == 200


@pytest.mark.django_db
def test_read_only_fields_ignored(logged_in, url, user):
    client, token = logged_in
    original_id = user.id
    res = patch(client, url, token, {
        "name": "Still Me",
        "role": "admin",
        "email": "attacker@example.com",
        "id": "00000000-0000-0000-0000-000000000000",
        "is_staff": True,
        "is_superuser": True,
        "is_active": False,
    })
    assert res.status_code == 200
    user.refresh_from_db()
    assert user.name == "Still Me"
    assert user.role == "user"
    assert user.email == "test@example.com"
    assert user.id == original_id
    assert not user.is_staff and not user.is_superuser
    assert user.is_active
    assert res.data["user"]["role"] == "user"


@pytest.mark.django_db
def test_other_users_data_unaffected(logged_in, url):
    other = User.objects.create_user(email="other@example.com", name="Other", avatar_url="https://x.example/o.png")
    client, token = logged_in
    res = patch(client, url, token, {"name": "Mine", "avatar_url": "https://cdn.example.com/m.png"})
    assert res.status_code == 200
    other.refresh_from_db()
    assert other.name == "Other"
    assert other.avatar_url == "https://x.example/o.png"


@pytest.mark.django_db
def test_profile_update_is_throttled(logged_in, url, settings):
    client, token = logged_in
    statuses = [patch(client, url, token, {"name": f"n{i}"}).status_code for i in range(22)]
    assert statuses[:20] == [200] * 20
    assert statuses[-1] == 429
    # GET (the session check) is never throttled by the profile scope.
    assert client.get(url).status_code == 200


# --------------------------------------------------------------------------
# Allowed methods (regression: a stale server answered PATCH with 405)
# --------------------------------------------------------------------------

@pytest.mark.django_db
def test_profile_allowed_methods(logged_in, url):
    client, token = logged_in
    assert client.get(url).status_code == 200
    assert patch(client, url, token, {"name": "Ok"}).status_code == 200

    options = client.options(url, HTTP_X_CSRFTOKEN=token)
    assert options.status_code == 200
    assert {"GET", "PATCH"} <= {m.strip() for m in options["Allow"].split(",")}


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["put", "post", "delete"])
def test_profile_other_methods_405_with_allow_header(logged_in, url, method, caplog):
    client, token = logged_in
    res = getattr(client, method)(url, {"name": "x"}, format="json", HTTP_X_CSRFTOKEN=token)
    assert res.status_code == 405
    allowed = {m.strip() for m in res["Allow"].split(",")}
    assert {"GET", "PATCH", "OPTIONS"} <= allowed and method.upper() not in allowed
    assert any(
        f"Method Not Allowed: {method.upper()} {url} (view=ProfileView" in r.getMessage()
        for r in caplog.records
    )


@pytest.mark.django_db
def test_cors_preflight_for_patch_allowed(api_client, url):
    """Cross-origin PATCH (direct-to-backend setups) passes CORS preflight."""
    res = api_client.options(
        url,
        HTTP_ORIGIN="http://localhost:5173",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="PATCH",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,x-csrftoken",
    )
    assert res.status_code == 200
    assert "PATCH" in res["Access-Control-Allow-Methods"]
    assert "x-csrftoken" in res["Access-Control-Allow-Headers"].lower()
    assert res["Access-Control-Allow-Credentials"] == "true"
