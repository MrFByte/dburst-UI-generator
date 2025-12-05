import pytest
import json
from unittest.mock import patch, MagicMock
from generation.cache import GenerationCache


@pytest.fixture
def mock_cache(mocker):
    """Mock Django cache backend for all tests."""
    return mocker.patch("generation.cache.cache")


@pytest.fixture
def sample_schema():
    return {"type": "Root", "props": {"className": "p-4"}}


@pytest.fixture
def sample_meta():
    return {"provider": "groq", "usage": {"total": 100}}


def test_store_generation_saves_all_keys(mock_cache, sample_schema, sample_meta):
    GenerationCache.store_generation(
        "abc123", sample_schema, "console.log('hi')", sample_meta
    )

    mock_cache.set.assert_any_call(
        "gen:abc123:schema",
        json.dumps(sample_schema),
        GenerationCache.TTL_DEFAULT,
    )

    mock_cache.set.assert_any_call(
        "gen:abc123:code",
        "console.log('hi')",
        GenerationCache.TTL_DEFAULT,
    )

    mock_cache.set.assert_any_call(
        "gen:abc123:meta",
        json.dumps(sample_meta),
        GenerationCache.TTL_DEFAULT,
    )


def test_get_generation_returns_full_data(mock_cache, sample_schema, sample_meta):
    mock_cache.get.side_effect = [
        json.dumps(sample_schema),
        "console.log('hi')",
        json.dumps(sample_meta),
    ]

    result = GenerationCache.get_generation("abc123")

    assert result["schema"] == sample_schema
    assert result["code"] == "console.log('hi')"
    assert result["meta"] == sample_meta


def test_get_generation_returns_none_if_missing_schema(mock_cache):
    """If schema is missing or empty, return None (invalid generation)."""
    mock_cache.get.side_effect = [None, None, None]

    result = GenerationCache.get_generation("missing")

    assert result is None


def test_get_generation_returns_none_if_missing_code(mock_cache, sample_schema):
    """Code is required along with schema."""
    mock_cache.get.side_effect = [
        json.dumps(sample_schema),
        None,
        None,
    ]

    assert GenerationCache.get_generation("abc123") is None


@patch("generation.cache.ReactCodeGenerator")
def test_apply_patch_success(mock_codegen, mock_cache, sample_schema):
    """Test JSON Patch flow + regenerated code update."""
    mock_cache.get.return_value = json.dumps(sample_schema)

    mock_instance = MagicMock()
    mock_instance.generate.return_value = "NEW_CODE"
    mock_codegen.return_value = mock_instance

    patch = [
        {"op": "replace", "path": "/props/className", "value": "p-10"},
    ]

    updated = {
        "type": "Root",
        "props": {"className": "p-10"},
    }

    from jsonpatch import apply_patch
    assert apply_patch(sample_schema, patch) == updated

    result = GenerationCache.apply_patch("abc123", patch)

    assert result == updated

    mock_cache.set.assert_any_call(
        "gen:abc123:schema",
        json.dumps(updated),
        GenerationCache.TTL_DEFAULT,
    )

    mock_cache.set.assert_any_call(
        "gen:abc123:code",
        "NEW_CODE",
        GenerationCache.TTL_DEFAULT,
    )


def test_apply_patch_returns_none_if_schema_missing(mock_cache):
    mock_cache.get.return_value = None
    assert GenerationCache.apply_patch("abc123", {}) is None


@patch("generation.cache.jsonpatch.apply_patch", side_effect=Exception("patch failed"))
def test_apply_patch_handles_failure(mock_apply, mock_cache, sample_schema):
    mock_cache.get.return_value = json.dumps(sample_schema)

    result = GenerationCache.apply_patch("abc123", {"op": "replace"})
    assert result is None
