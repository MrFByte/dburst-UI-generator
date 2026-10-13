"""The inline-edit flow exactly as the browser drives it: cookie auth + CSRF,
patch -> history -> version -> undo. No LLM involved."""
import pytest
from django.urls import reverse

from generation.models import Generations
from projects.models import Project
from users.models import User
from users.tests.conftest import fetch_csrf, login_with_cookies

SCHEMA = {"type": "Root", "children": [
    {"type": "Text", "props": {"tag": "h1", "className": "text-4xl"}, "content": "Hello world"},
    {"type": "Grid", "props": {"className": "grid grid-cols-3 gap-6"}, "children": []},
]}


@pytest.fixture
def owner(db):
    return User.objects.create_user(email="owner@example.com", name="Owner")


@pytest.fixture
def generation(owner):
    project = Project.objects.create(user=owner, title="Demo")
    return Generations.objects.create(project=project, prompt="p", schema=SCHEMA, llm_provider="groq", status="success")


@pytest.fixture
def browser(owner):
    from rest_framework.test import APIClient
    client = APIClient(enforce_csrf_checks=True)
    token = fetch_csrf(client)
    login_with_cookies(client, owner)
    return client, token


@pytest.mark.django_db
def test_project_detail_exposes_generation_id(browser, generation):
    client, _ = browser
    res = client.get(reverse("project-detail", args=[generation.project.id]))
    assert res.status_code == 200
    assert str(res.data["latest_generation"]["id"]) == str(generation.id)
    assert "Hello world" in res.data["latest_generation"]["code"]


@pytest.mark.django_db
def test_inline_edit_patch_flow_with_cookie_auth_and_csrf(browser, generation):
    client, token = browser
    gid = generation.id
    patch = [{"op": "replace", "path": "/children/0/content", "value": "Hello edited"}]

    # Without CSRF the browser's save is rejected...
    assert client.post(reverse("store-patch", args=[gid]), {"patch": patch}, format="json").status_code == 403

    # ...with it, the patch applies and returns schema + regenerated code.
    res = client.post(reverse("store-patch", args=[gid]), {"patch": patch, "description": "Manual save"},
                      format="json", HTTP_X_CSRFTOKEN=token)
    assert res.status_code == 200, res.data
    assert res.data["schema"]["children"][0]["content"] == "Hello edited"
    assert "Hello edited" in res.data["code"] and "Hello world" not in res.data["code"]
    patch_id = res.data["patch_id"]

    history = client.get(reverse("list-patches", args=[gid]))
    assert history.status_code == 200
    assert history.data["total_patches"] == 1
    assert history.data["patches"][0]["description"] == "Manual save"

    schema = client.get(reverse("get-schema", args=[gid]))
    assert schema.status_code == 200
    assert schema.data["schema"]["children"][0]["content"] == "Hello edited"

    version = client.get(reverse("get-version", args=[gid, patch_id]))
    assert version.status_code == 200
    assert version.data["schema"]["children"][0]["content"] == "Hello edited"
    assert "Hello edited" in version.data["code"]

    undo = client.post(reverse("undo-patch", args=[gid]), format="json", HTTP_X_CSRFTOKEN=token)
    assert undo.status_code == 200
    assert undo.data["schema"]["children"][0]["content"] == "Hello world"


@pytest.mark.django_db
def test_structurally_invalid_patch_is_rejected_not_stored(browser, generation):
    client, token = browser
    bad = [{"op": "add", "path": "/children/-", "value": {"type": "Card", "children": "nope"}}]
    res = client.post(reverse("store-patch", args=[generation.id]), {"patch": bad}, format="json", HTTP_X_CSRFTOKEN=token)
    assert res.status_code >= 400
    assert generation.patches.count() == 0


@pytest.mark.django_db
def test_patch_endpoints_require_login(generation):
    from rest_framework.test import APIClient
    client = APIClient(enforce_csrf_checks=True)
    assert client.get(reverse("list-patches", args=[generation.id])).status_code == 401
    assert client.get(reverse("get-schema", args=[generation.id])).status_code == 401
