"""
API error contract: friendly message + stable code, raw provider payloads and
exception text only in logs. LLM HTTP is mocked; nothing calls a real provider.
"""
import json
import logging
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.urls import reverse

from generation.models import Generations
from projects.models import Project

FAKE_GEMINI_KEY = "AIzaSyTESTKEY0000000000000000000000000"
FAKE_GROQ_KEY = "gsk_TESTKEY000000000000000000000000"

GEMINI_400 = {"error": {"code": 400, "message": "Request contains an invalid argument.", "status": "INVALID_ARGUMENT"}}

FRIENDLY = {
    "llm_bad_request": "The AI model couldn't process this request. Try rephrasing your prompt, shortening it, or choosing a different model.",
    "llm_quota": "This model is temporarily unavailable. Please choose a different model.",
    "llm_timeout": "The model took too long to respond. Try again, or use a faster model or a simpler prompt.",
    "llm_content_blocked": "The AI couldn't generate this because of its content policy. Try a different description.",
    "llm_invalid_response": "The AI returned an incomplete design. Please try again.",
}


def http_response(status, body=None, text=None, headers=None):
    resp = MagicMock()
    resp.status_code = status
    resp.headers = headers or {}
    if body is not None:
        resp.json.return_value = body
        resp.text = json.dumps(body)
    else:
        resp.json.side_effect = ValueError("no json")
        resp.text = text or ""
    return resp


def gemini_ok(text, finish="STOP"):
    return http_response(200, {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": finish}]})


@pytest.fixture(autouse=True)
def fake_keys_and_no_sleep(monkeypatch):
    monkeypatch.setattr("generation.llm.GEMINI_API_KEY", FAKE_GEMINI_KEY)
    monkeypatch.setattr("generation.llm.GROQ_API_KEY", FAKE_GROQ_KEY)
    monkeypatch.setattr("generation.llm_chat.GEMINI_API_KEY", FAKE_GEMINI_KEY)
    monkeypatch.setattr("generation.llm_chat.GROQ_API_KEY", FAKE_GROQ_KEY)
    monkeypatch.setattr("generation.llm.time.sleep", lambda s: None)


@pytest.fixture
def client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


def generate(client, model="gemini:models/gemini-3.8-flash"):
    return client.post(reverse("generate"), {"prompt": "A pet store", "ui_model": model}, format="json")


def assert_clean(res, *forbidden):
    """No raw provider JSON, provider status names, keys or exception text."""
    body = json.dumps(res.data)
    for needle in ("INVALID_ARGUMENT", "RESOURCE_EXHAUSTED", '"status":', "API Error", "Traceback",
                   FAKE_GEMINI_KEY, FAKE_GROQ_KEY, "{\\\"error\\\"", *forbidden):
        assert needle not in body, (needle, body)
    assert set(res.data) <= {"error", "code", "details", "retry_after", "request_id"}
    assert res.data["request_id"]  # RequestIdMiddleware -> shown for support


# --------------------------------------------------------------------------
# Gemini
# --------------------------------------------------------------------------

@pytest.mark.django_db
def test_gemini_invalid_argument_is_friendly_and_logged(client, caplog):
    caplog.set_level(logging.ERROR)
    with patch("generation.llm.requests.post", return_value=http_response(400, GEMINI_400)) as post:
        res = generate(client)

    assert res.status_code == 502
    assert res.data["code"] == "llm_bad_request"
    assert res.data["error"] == FRIENDLY["llm_bad_request"]
    assert_clean(res, "Request contains an invalid argument")
    assert post.call_count == 1  # a rejected request is not retried

    # Raw payload goes to the logs, the key never does (header, not URL).
    logs = caplog.text
    assert "INVALID_ARGUMENT" in logs and "Request contains an invalid argument." in logs
    assert FAKE_GEMINI_KEY not in logs
    url = post.call_args.args[0]
    assert "key=" not in url and FAKE_GEMINI_KEY not in url
    assert post.call_args.kwargs["headers"]["x-goog-api-key"] == FAKE_GEMINI_KEY


@pytest.mark.django_db
def test_gemini_api_key_invalid_maps_to_quota(client):
    body = {"error": {"code": 400, "message": "API key not valid. Please pass a valid API key.", "status": "INVALID_ARGUMENT",
                      "details": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "API_KEY_INVALID"}]}}
    with patch("generation.llm.requests.post", return_value=http_response(400, body)):
        res = generate(client)
    assert res.status_code == 502 and res.data["code"] == "llm_quota"
    assert res.data["error"] == FRIENDLY["llm_quota"]
    assert_clean(res, "API key")


@pytest.mark.django_db
def test_gemini_rate_limit_carries_retry_after(client):
    body = {"error": {"code": 429, "message": "Resource has been exhausted (e.g. check quota).", "status": "RESOURCE_EXHAUSTED",
                      "details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "12s"}]}}
    with patch("generation.llm.requests.post", return_value=http_response(429, body)):
        res = generate(client)
    assert res.status_code == 429
    assert res.data["code"] == "llm_rate_limited"
    assert res.data["retry_after"] == 12
    assert res["Retry-After"] == "12"
    assert res.data["error"] == "The model is busy right now. Please wait 12 seconds and try again, or pick another model."
    assert_clean(res)


@pytest.mark.django_db
def test_gemini_daily_quota_is_quota_not_rate_limit(client):
    body = {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED",
                      "message": "Quota exceeded for metric: generate_content_free_tier_requests, limit: 0, model: x",
                      "details": [{"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}]}}
    with patch("generation.llm.requests.post", return_value=http_response(429, body)):
        res = generate(client)
    assert res.status_code == 502 and res.data["code"] == "llm_quota"
    assert_clean(res, "Quota exceeded")


@pytest.mark.django_db
def test_gemini_503_is_retried_then_unavailable(client):
    body = {"error": {"code": 503, "message": "The model is overloaded.", "status": "UNAVAILABLE"}}
    with patch("generation.llm.requests.post", return_value=http_response(503, body)) as post:
        res = generate(client)
    assert res.status_code == 503 and res.data["code"] == "llm_unavailable"
    assert post.call_count == 3  # retriable
    assert_clean(res, "overloaded")


@pytest.mark.django_db
@pytest.mark.parametrize("side_effect,status_code,code", [
    (requests.exceptions.ReadTimeout(f"HTTPSConnectionPool: Read timed out. url=...?key={FAKE_GEMINI_KEY}"), 504, "llm_timeout"),
    (requests.exceptions.ConnectionError("Max retries exceeded with url"), 503, "llm_unavailable"),
])
def test_gemini_transport_errors(client, caplog, side_effect, status_code, code):
    caplog.set_level(logging.ERROR)
    with patch("generation.llm.requests.post", side_effect=side_effect):
        res = generate(client)
    assert res.status_code == status_code and res.data["code"] == code
    assert_clean(res, "timed out", "Max retries")
    assert FAKE_GEMINI_KEY not in caplog.text  # scrubbed even when an exception embeds it


@pytest.mark.django_db
def test_gemini_504_status_is_timeout(client):
    body = {"error": {"code": 504, "message": "Deadline expired", "status": "DEADLINE_EXCEEDED"}}
    with patch("generation.llm.requests.post", return_value=http_response(504, body)):
        res = generate(client)
    assert res.status_code == 504 and res.data["error"] == FRIENDLY["llm_timeout"]


@pytest.mark.django_db
@pytest.mark.parametrize("payload", [
    {"candidates": [{"finishReason": "SAFETY", "safetyRatings": [{"category": "HARM_CATEGORY_X", "probability": "HIGH"}]}]},
    {"candidates": [{"finishReason": "RECITATION"}]},
    {"promptFeedback": {"blockReason": "SAFETY"}},
])
def test_gemini_content_blocks(client, payload):
    with patch("generation.llm.requests.post", return_value=http_response(200, payload)) as post:
        res = generate(client)
    assert res.status_code == 422
    assert res.data["code"] == "llm_content_blocked"
    assert res.data["error"] == FRIENDLY["llm_content_blocked"]
    assert post.call_count == 1
    assert_clean(res, "HARM_CATEGORY", "SAFETY", "RECITATION")


@pytest.mark.django_db
@pytest.mark.parametrize("response", [
    gemini_ok('{"project_name": "x", "project_description": '),   # truncated JSON
    gemini_ok("Sorry, I can't produce JSON today."),               # prose
    gemini_ok("[1, 2, 3]"),                                        # not an object
    http_response(200, text="<html>bad gateway</html>"),           # non-JSON 200
    http_response(200, {"candidates": []}),                        # empty
])
def test_gemini_invalid_output(client, response):
    with patch("generation.llm.requests.post", return_value=response):
        res = generate(client)
    assert res.status_code == 502
    assert res.data["code"] == "llm_invalid_response"
    assert res.data["error"] == FRIENDLY["llm_invalid_response"]
    assert_clean(res, "Expecting", "JSONDecodeError", "<html>")


# --------------------------------------------------------------------------
# Groq
# --------------------------------------------------------------------------

def groq_error(status, message, type_="invalid_request_error", code=None, headers=None):
    return http_response(status, {"error": {"message": message, "type": type_, "code": code}}, headers=headers)


@pytest.mark.django_db
@pytest.mark.parametrize("response,status_code,code", [
    (groq_error(400, "messages: content too long", code="context_length_exceeded"), 502, "llm_bad_request"),
    (groq_error(413, "Request too large for model", type_="tokens"), 502, "llm_bad_request"),
    (groq_error(401, "Invalid API Key", code="invalid_api_key"), 502, "llm_quota"),
    (groq_error(404, "The model `x` does not exist", code="model_not_found"), 503, "llm_unavailable"),
    (groq_error(429, "Rate limit reached for model. Please try again in 7.66s.", type_="tokens",
                code="rate_limit_exceeded", headers={"retry-after": "8"}), 429, "llm_rate_limited"),
    (groq_error(503, "Service Unavailable", type_="internal_server_error"), 503, "llm_unavailable"),
    (http_response(502, text="<html><body>502 Bad Gateway</body></html>"), 503, "llm_unavailable"),
])
def test_groq_errors(client, caplog, response, status_code, code):
    caplog.set_level(logging.ERROR)
    with patch("generation.llm.requests.post", return_value=response):
        res = generate(client, model="groq:openai/gpt-oss-20b")
    assert res.status_code == status_code and res.data["code"] == code
    assert_clean(res, "invalid_request_error", "Invalid API Key", "rate_limit_exceeded", "<html>")
    assert "groq API error: status=" in caplog.text
    assert FAKE_GROQ_KEY not in caplog.text


@pytest.mark.django_db
def test_groq_rate_limit_uses_retry_after_header(client):
    resp = groq_error(429, "Rate limit reached", code="rate_limit_exceeded", headers={"retry-after": "8"})
    with patch("generation.llm.requests.post", return_value=resp):
        res = generate(client, model="groq:openai/gpt-oss-20b")
    assert res.data["retry_after"] == 8 and res["Retry-After"] == "8"


@pytest.mark.django_db
def test_groq_content_filter(client):
    resp = http_response(200, {"choices": [{"finish_reason": "content_filter", "message": {"content": ""}}]})
    with patch("generation.llm.requests.post", return_value=resp):
        res = generate(client, model="groq:openai/gpt-oss-20b")
    assert res.status_code == 422 and res.data["code"] == "llm_content_blocked"


# --------------------------------------------------------------------------
# Refine (separate client in llm_chat.py)
# --------------------------------------------------------------------------

@pytest.fixture
def generation(user):
    project = Project.objects.create(user=user, title="P")
    return Generations.objects.create(project=project, prompt="p", schema={"type": "Root"}, llm_provider="gemini",
                                      status="success", metadata={"ui_model": "gemini:models/gemini-3.8-flash"})


@pytest.mark.django_db
def test_refine_gemini_invalid_argument(client, generation, caplog):
    caplog.set_level(logging.ERROR)
    with patch("generation.llm_chat.requests.post", return_value=http_response(400, GEMINI_400)) as post:
        res = client.post(reverse("refine-ui"), {"generation_id": str(generation.id), "message": "make it blue"}, format="json")
    assert res.status_code == 502 and res.data["code"] == "llm_bad_request"
    assert_clean(res, "Failed to refine UI", "Request contains")
    assert "INVALID_ARGUMENT" in caplog.text
    assert "key=" not in post.call_args.args[0]


@pytest.mark.django_db
def test_refine_missing_fields_is_validation_error(client):
    res = client.post(reverse("refine-ui"), {"message": "x"}, format="json")
    assert res.status_code == 400
    assert res.data["code"] == "validation_error"
    assert res.data["details"] == {"generation_id": ["This field is required."]}


# --------------------------------------------------------------------------
# Exception handler: DRF exceptions and the catch-all
# --------------------------------------------------------------------------

@pytest.mark.django_db
def test_unhandled_exception_is_generic_500_with_request_id(client, caplog):
    caplog.set_level(logging.ERROR)
    with patch("generation.views.LLMClient", side_effect=RuntimeError("db password is hunter2")):
        res = generate(client)
    assert res.status_code == 500
    assert res.data["code"] == "server_error"
    assert res.data["error"] == "Something went wrong on our side. Please try again."
    assert_clean(res, "hunter2", "RuntimeError")
    assert res["X-Request-ID"] == res.data["request_id"]
    assert "hunter2" in caplog.text and "Traceback" in caplog.text  # full detail in logs


@pytest.mark.django_db
def test_validation_error_shape(client):
    res = client.post(reverse("generate"), {"prompt": "   ", "ui_model": "nope:nope"}, format="json")
    assert res.status_code == 400
    assert res.data["code"] == "validation_error"
    assert set(res.data["details"]) == {"prompt", "ui_model"}
    assert res.data["error"] == "Please check the highlighted fields and try again."


@pytest.mark.django_db
def test_single_field_error_is_shown_directly(client):
    res = client.post(reverse("generate"), {"prompt": "   "}, format="json")
    # DRF's generic message gets the field name when shown on its own.
    assert res.data["error"] == "Prompt may not be blank."
    assert res.data["details"] == {"prompt": ["This field may not be blank."]}


@pytest.mark.django_db
def test_throttled_includes_retry_after(api_client, settings):
    settings.OTP_MAX_REQUESTS_PER_WINDOW = 100
    with patch("otp_auth.views.send_otp_email"):
        responses = [api_client.post(reverse("otp-request"), {"email": f"u{i}@example.com"}, format="json") for i in range(6)]
    res = responses[-1]
    assert res.status_code == 429
    assert res.data["code"] == "throttled"
    assert isinstance(res.data["retry_after"], int) and res.data["retry_after"] >= 1
    assert res["Retry-After"] == str(res.data["retry_after"])
    assert f"{res.data['retry_after']} seconds" in res.data["error"]


@pytest.mark.django_db
def test_not_authenticated_shape(api_client):
    res = api_client.get(reverse("user-profile"))
    assert res.status_code == 401
    assert res.data["code"] == "not_authenticated"
    assert res.data["error"] == "Please sign in to continue."


@pytest.mark.django_db
def test_parse_error_is_friendly(client):
    res = client.generic("POST", reverse("generate"), "{not json", content_type="application/json")
    assert res.status_code == 400 and res.data["code"] == "bad_request"
    assert "JSON parse error" not in res.data["error"]


@pytest.mark.django_db
def test_method_not_allowed_shape(client):
    res = client.delete(reverse("user-profile"))
    assert res.status_code == 405 and res.data["code"] == "method_not_allowed"


@pytest.mark.django_db
def test_unknown_api_path_is_json(client):
    res = client.get("/api/v1/definitely-not-a-route/")
    assert res.status_code == 404
    body = json.loads(res.content)
    assert body["code"] == "not_found" and "<html" not in res.content.decode().lower()


@pytest.mark.django_db
def test_otp_errors_keep_wording_and_gain_code(api_client):
    res = api_client.post(reverse("otp-verify"), {"email": "a@example.com", "code": "123456"}, format="json")
    assert res.status_code == 400
    assert res.data["error"] == "Invalid or expired OTP."
    assert res.data["code"] == "otp_invalid"
