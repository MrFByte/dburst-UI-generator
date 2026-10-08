import pytest
import json
from unittest.mock import patch, MagicMock
from generation.llm import LLMClient

def mock_llm_response(content_dict):
    """Factory for standard LLM response format."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "choices": [
            {"message": {"content": json.dumps(content_dict)}}
        ],
        "usage": {"total_tokens": 100}
    }
    return mock

def test_invalid_model_raises_value_error():
    """Initializing with an unknown model id should raise ValueError."""
    with pytest.raises(ValueError):
        LLMClient(ui_model_id="groq:invalid-model")

def test_malformed_model_id_raises_value_error():
    """A model id missing the 'provider:' prefix should raise ValueError."""
    with pytest.raises(ValueError):
        LLMClient(ui_model_id="no-colon-here")

@patch("generation.llm.LLMClient._call_planner")
@patch("generation.llm.LLMClient._call_ui_generator")
def test_generate_ui_flow(mock_ui, mock_planner):
    """Test the two-stage generation flow."""
    # Setup mocks
    mock_planner.return_value = {
        "project_name": "Test Project",
        "project_description": "Desc",
        "design_plan": {},
        "usage": {"total_tokens": 50}
    }
    mock_ui.return_value = {
        "title": "Generated UI",
        "schema": {"type": "Root"},
        "metadata": {"framework": "react"},
        "usage": {"total_tokens": 100}
    }

    client = LLMClient(ui_model_id="groq:openai/gpt-oss-20b")
    result = client.generate_ui("Make a dashboard")

    # Assertions
    assert result["project_name"] == "Test Project"
    assert result["title"] == "Generated UI"
    assert result["models"]["provider"] == "groq"
    assert result["models"]["ui_generation"] == "groq:openai/gpt-oss-20b"
    assert result["models"]["planning"] == "groq:openai/gpt-oss-120b"
    assert result["usage"]["planning_tokens"]["total_tokens"] == 50
    assert result["usage"]["generation_tokens"]["total_tokens"] == 100

    mock_planner.assert_called_once()
    mock_ui.assert_called_once()

@patch("generation.llm.requests.post")
def test_call_groq_api_success(mock_post):
    """Test direct API call wrapper for Groq."""
    mock_post.return_value = mock_llm_response({"key": "value"})

    client = LLMClient(ui_model_id="groq:openai/gpt-oss-20b")
    # We test the internal method since generate_ui is complex
    result = client._call_groq_api("prompt", "system", "model-id")

    assert result["key"] == "value"
    assert result["usage"]["total_tokens"] == 100

@patch("generation.llm.requests.post")
def test_call_gemini_api_success(mock_post):
    """Test direct API call wrapper for Gemini."""
    # Gemini has different response structure
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "candidates": [
            {"content": {"parts": [{"text": json.dumps({"key": "val"})}]}}
        ],
        "usageMetadata": {"totalTokenCount": 50}
    }
    mock_post.return_value = mock

    client = LLMClient(ui_model_id="gemini:models/gemini-3.8-flash")
    result = client._call_gemini("prompt", "system", "models/gemini-3.8-flash")

    assert result["key"] == "val"
    assert result["usage"]["totalTokenCount"] == 50

    called_url = mock_post.call_args.args[0]
    assert "models/gemini-3.8-flash:generateContent" in called_url

def test_parse_response_fixes_json():
    """Test JSON recovery logic."""
    client = LLMClient()

    truncated_json = '{"schema": {"type": "Root", "props": {'

    valid_json = '```json\n{"a": 1}\n```'
    parsed = client._parse_response(valid_json, {})
    assert parsed["a"] == 1

@patch("generation.llm.requests.post")
def test_api_failure_handling(mock_post):
    """Test that API errors are raised."""
    mock_post.return_value.status_code = 500
    mock_post.return_value.text = "Error"

    client = LLMClient(ui_model_id="groq:openai/gpt-oss-20b")

    with pytest.raises(ValueError) as exc:
        client._call_groq_api("p", "s", "m")

    assert "Groq API Error (500)" in str(exc.value)
