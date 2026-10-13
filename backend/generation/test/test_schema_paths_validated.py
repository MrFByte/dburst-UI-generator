"""Every path that turns a schema into code validates it first."""
import json
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.urls import reverse

from generation.cache import GenerationCache
from generation.models import Generations
from projects.models import Project


@pytest.fixture
def generation(user):
    project = Project.objects.create(user=user, title="p")
    return Generations.objects.create(
        project=project, prompt="make a page", schema={"type": "Root", "children": []},
        llm_provider="groq", status="success",
    )


def refine(api_client, user, generation, result):
    api_client.force_authenticate(user=user)
    with patch("generation.views_chat.LLMChat") as chat_cls:
        chat_cls.return_value.refine_ui.return_value = result
        return api_client.post(
            reverse("refine-ui"),
            {"generation_id": str(generation.id), "message": "change it"},
            format="json",
        )


@pytest.mark.django_db
def test_refine_rejects_invalid_schema_with_400(api_client, user, generation):
    res = refine(api_client, user, generation, {
        "schema": {"type": "Root", "props": "not-a-dict"}, "ai_response": "done", "usage": {},
    })
    assert res.status_code == 400
    assert res.data["error"].startswith("Schema validation failed:")
    generation.refresh_from_db()
    assert generation.schema == {"type": "Root", "children": []}  # not overwritten


@pytest.mark.django_db
def test_refine_validates_and_escapes(api_client, user, generation):
    res = refine(api_client, user, generation, {
        "schema": {"type": "Root", "children": [
            {"type": "Paragraph", "props": {"className": "  p-4   dark:bg-black "}, "content": "{x}"},
        ]},
        "ai_response": "done", "usage": {"total_tokens": 5},
    })
    assert res.status_code == 200
    child = res.data["schema"]["children"][0]
    assert child["type"] == "Text"  # normalized by the validator
    assert child["props"]["className"] == "p-4 dark:bg-black"
    assert '<p className="p-4 dark:bg-black">&#123;x&#125;</p>' in res.data["code"]
    generation.refresh_from_db()
    assert generation.schema["children"][0]["type"] == "Text"


def test_apply_patch_rejects_structurally_invalid_result():
    cache.set("gen:g1:schema", json.dumps({"type": "Root", "children": []}))
    cache.set("gen:g1:code", "old")
    bad = [{"op": "add", "path": "/children/-", "value": {"type": "Card", "children": "nope"}}]
    assert GenerationCache.apply_patch("g1", bad) is None
    assert json.loads(cache.get("gen:g1:schema")) == {"type": "Root", "children": []}
    assert cache.get("gen:g1:code") == "old"


def test_apply_patch_escapes_hostile_values():
    cache.set("gen:g2:schema", json.dumps({"type": "Root", "children": []}))
    hostile = [{"op": "add", "path": "/children/-", "value": {
        "type": "Link", "props": {"href": "javascript:alert(1)", "className": 'a"onClick={x}'}, "content": "{y}"}}]
    assert GenerationCache.apply_patch("g2", hostile) is not None
    code = cache.get("gen:g2:code")
    assert "javascript:" not in code and 'className="a"onClick' not in code and "{y}" not in code
