import pytest
import json
from unittest.mock import patch, MagicMock
from generation.cache import GenerationCache


@pytest.fixture
def mock_redis(mocker):
    """Mock Redis connection for all tests."""
    return mocker.patch("generation.cache.get_redis_connection")


@pytest.fixture
def mock_cache(mocker):
    """Mock Django cache backend."""
    return mocker.patch("generation.cache.cache")


@pytest.fixture
def sample_patch():
    return [{"op": "replace", "path": "/props/className", "value": "p-10"}]


def test_store_patch_success(mock_redis, mock_cache):
    """Test successful patch storage in Redis"""
    mock_conn = MagicMock()
    mock_redis.return_value = mock_conn
    mock_conn.llen.return_value = 0  # No existing patches
    
    result = GenerationCache.store_patch(
        "test-gen-id",
        [{"op": "replace", "path": "/props/className", "value": "p-10"}],
        "user-123",
        "Changed padding"
    )
    
    assert result is True
    mock_conn.lpush.assert_called_once()
    mock_conn.expire.assert_called_once()


def test_store_patch_with_snapshot_threshold(mock_redis, mock_cache):
    """Test that snapshot flag is logged at threshold"""
    mock_conn = MagicMock()
    mock_redis.return_value = mock_conn
    mock_conn.llen.return_value = 9  # 9 existing patches, next will be 10th
    
    result = GenerationCache.store_patch(
        "test-gen-id",
        [{"op": "add", "path": "/children/-", "value": {"type": "Text"}}],
        "user-123",
        "Added text component"
    )
    
    assert result is True
    # Snapshot threshold (10) should be reached


def test_get_patches_returns_list(mock_redis):
    """Test retrieving patch list from Redis"""
    mock_conn = MagicMock()
    mock_redis.return_value = mock_conn
    
    patch_data = {
        "patch": [{"op": "replace", "path": "/props/className", "value": "p-10"}],
        "user_id": "user-123",
        "description": "Test patch",
        "timestamp": 1234567890.0
    }
    
    mock_conn.lrange.return_value = [json.dumps(patch_data).encode()]
    
    patches = GenerationCache.get_patches("test-gen-id", limit=10)
    
    assert len(patches) == 1
    assert patches[0]["user_id"] == "user-123"
    assert patches[0]["description"] == "Test patch"


def test_get_patches_with_pagination(mock_redis):
    """Test patch retrieval with pagination"""
    mock_conn = MagicMock()
    mock_redis.return_value = mock_conn
    mock_conn.lrange.return_value = []
    
    patches = GenerationCache.get_patches("test-gen-id", limit=20, offset=10)
    
    mock_conn.lrange.assert_called_once_with("gen:test-gen-id:patches", 10, 29)


def test_get_patch_count(mock_redis):
    """Test getting total patch count"""
    mock_conn = MagicMock()
    mock_redis.return_value = mock_conn
    mock_conn.llen.return_value = 15
    
    count = GenerationCache.get_patch_count("test-gen-id")
    
    assert count == 15
    mock_conn.llen.assert_called_once_with("gen:test-gen-id:patches")


def test_get_schema_from_cache(mock_cache):
    """Test retrieving schema from cache"""
    sample_schema = {"type": "Root", "props": {"className": "p-4"}}
    mock_cache.get.return_value = json.dumps(sample_schema)
    
    schema = GenerationCache.get_schema("test-gen-id")
    
    assert schema == sample_schema
    mock_cache.get.assert_called_once_with("gen:test-gen-id:schema")


def test_get_schema_not_found(mock_cache):
    """Test schema retrieval when not in cache"""
    mock_cache.get.return_value = None
    
    schema = GenerationCache.get_schema("test-gen-id")
    
    assert schema is None


def test_clear_generation(mock_redis, mock_cache):
    """Test clearing all cached data for a generation"""
    mock_conn = MagicMock()
    mock_redis.return_value = mock_conn
    
    result = GenerationCache.clear_generation("test-gen-id")
    
    assert result is True
    assert mock_cache.delete.call_count == 3  # schema, code, meta
    mock_conn.delete.assert_called_once_with("gen:test-gen-id:patches")


def test_store_patch_handles_error(mock_redis):
    """Test error handling in patch storage"""
    mock_redis.side_effect = Exception("Redis connection failed")
    
    result = GenerationCache.store_patch(
        "test-gen-id",
        [{"op": "replace", "path": "/props/className", "value": "p-10"}],
        "user-123"
    )
    
    assert result is False


def test_get_patches_handles_invalid_json(mock_redis):
    """Test handling of corrupted patch data"""
    mock_conn = MagicMock()
    mock_redis.return_value = mock_conn
    mock_conn.lrange.return_value = [b"invalid json", b'{"valid": "json"}']
    
    patches = GenerationCache.get_patches("test-gen-id")
    
    # Should skip invalid JSON and return only valid patches
    assert len(patches) == 1
    assert patches[0]["valid"] == "json"
