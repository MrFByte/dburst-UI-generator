import pytest
import json
from unittest.mock import patch, MagicMock

from generation.llm import LLMClient, SYSTEM_PROMPT


def mock_groq_success(content_json: dict):
    """Mock a valid Groq response."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(content_json)
                }
            }
        ],
        "usage": {
            "total_tokens": 100,
            "prompt_tokens": 50,
            "completion_tokens": 50,
        }
    }
    return mock


def mock_gemini_success(content_json: dict):
    """Mock a valid Gemini response."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": json.dumps(content_json)}
                    ]
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 20,
            "candidatesTokenCount": 30,
        }
    }
    return mock


def test_invalid_provider_raises_value_error():
    client = LLMClient(provider="invalid-provider")

    with pytest.raises(ValueError):
        client.call("hello")


@patch("generation.llm.requests.post")
def test_groq_success(mock_post):
    """Ensure LLMClient correctly parses a Groq response."""
    mock_content = {
        "title": "Dashboard",
        "schema": {"type": "Root"},
        "metadata": {"framework": "react"},
        "code": "<div />"
    }

    mock_post.return_value = mock_groq_success(mock_content)

    client = LLMClient(provider="groq")
    result = client.call("Generate UI")

    assert result["provider"] == "groq"
    assert result["title"] == "Dashboard"
    assert result["schema"]["type"] == "Root"
    assert result["usage"]["total_tokens"] == 100


@patch("generation.llm.requests.post")
def test_gemini_success(mock_post):
    """Ensure LLMClient correctly parses a Gemini response."""
    mock_content = {
        "title": "Landing Page",
        "schema": {"type": "Root"},
        "metadata": {"framework": "react"},
    }

    mock_post.return_value = mock_gemini_success(mock_content)

    client = LLMClient(provider="gemini")
    result = client.call("Generate UI")

    assert result["provider"] == "gemini"
    assert result["title"] == "Landing Page"
    assert result["schema"]["type"] == "Root"
    assert "usageMetadata" not in result


@patch("generation.llm.requests.post")
def test_retry_logic(mock_post):
    """First two calls fail, third succeeds."""
    mock_post.side_effect = [
        Exception("Network error"),
        Exception("Timeout"),
        mock_groq_success({"title": "Recovered"})
    ]

    client = LLMClient(provider="groq")

    result = client.call("retry test", retries=3)

    assert result["title"] == "Recovered"
    assert mock_post.call_count == 3


@patch("generation.llm.requests.post")
def test_retry_exhaustion_raises(mock_post):
    """All attempts fail → final error should bubble up."""
    mock_post.side_effect = Exception("Still failing...")

    client = LLMClient(provider="groq")

    with pytest.raises(Exception):
        client.call("fail-test", retries=3)

    assert mock_post.call_count == 3


@patch("generation.llm.requests.post")
def test_groq_http_error(mock_post):
    """Non-200 status code should raise ValueError."""
    mock = MagicMock()
    mock.status_code = 500
    mock.text = "Server Error"

    mock_post.return_value = mock

    client = LLMClient(provider="groq")

    with pytest.raises(ValueError):
        client.call("hello")


@patch("generation.llm.requests.post")
def test_parse_json_code_block(mock_post):
    """Ensure parser extracts JSON inside ```json blocks."""
    response_text = """```json
    {
      "title": "Card UI",
      "schema": {"type": "Root"}
    }
    ```"""

    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "choices": [
            {
                "message": {"content": response_text}
            }
        ],
        "usage": {}
    }

    mock_post.return_value = mock

    client = LLMClient(provider="groq")
    result = client.call("test")

    assert result["title"] == "Card UI"
    assert result["schema"]["type"] == "Root"


@patch("generation.llm.requests.post")
def test_invalid_json_raises(mock_post):
    """Invalid JSON from model should raise ValueError."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "choices": [
            {
                "message": {"content": "{ invalid json ... "}
            }
        ],
        "usage": {}
    }

    mock_post.return_value = mock

    client = LLMClient(provider="groq")

    with pytest.raises(ValueError):
        client.call("test")


def test_parse_response_keeps_defaults():
    """Missing optional fields should still return stable defaults."""
    client = LLMClient()

    parsed = client._parse_response(
        content=json.dumps({"schema": {"type": "Root"}}),
        usage={},
        provider="groq"
    )

    assert parsed["title"] == "Generated UI"
    assert parsed["schema"]["type"] == "Root"
    assert parsed["metadata"] == {}
