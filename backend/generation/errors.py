"""
Typed, user-safe errors for LLM generation, and the mapping from provider
(Gemini / Groq) HTTP responses to them.

The raw provider payload never reaches the client: it is logged here (with
API keys scrubbed) and the client gets one of the friendly messages below.
"""
import contextlib
import json
import logging
import re
from typing import Any, Optional

import requests
from rest_framework import status as http

from config.api_errors import ApiError

logger = logging.getLogger("generation.llm.errors")

DEFAULT_RETRY_AFTER = 30


class LLMError(ApiError):
    status_code = http.HTTP_502_BAD_GATEWAY
    default_code = "llm_error"
    default_detail = "The AI model ran into a problem. Please try again, or choose a different model."
    retriable = False


class LLMBadRequestError(LLMError):
    default_code = "llm_bad_request"
    default_detail = ("The AI model couldn't process this request. Try rephrasing your prompt, "
                      "shortening it, or choosing a different model.")


class LLMRateLimitError(LLMError):
    status_code = http.HTTP_429_TOO_MANY_REQUESTS
    default_code = "llm_rate_limited"

    def __init__(self, retry_after: Optional[float] = None, **kwargs):
        retry_after = retry_after or DEFAULT_RETRY_AFTER
        seconds = max(1, int(round(retry_after)))
        message = (f"The model is busy right now. Please wait {seconds} seconds and try again, "
                   "or pick another model.")
        super().__init__(message, retry_after=seconds, **kwargs)


class LLMUnavailableError(LLMError):
    status_code = http.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "llm_unavailable"
    default_detail = "This model is temporarily unavailable. Please try again shortly or choose a different model."
    retriable = True


class LLMQuotaError(LLMError):
    """Bad/missing/expired key, billing or quota problems. Never say which."""
    default_code = "llm_quota"
    default_detail = "This model is temporarily unavailable. Please choose a different model."


class LLMTimeoutError(LLMError):
    status_code = http.HTTP_504_GATEWAY_TIMEOUT
    default_code = "llm_timeout"
    default_detail = ("The model took too long to respond. Try again, or use a faster model "
                      "or a simpler prompt.")
    retriable = True


class LLMContentBlockedError(LLMError):
    status_code = http.HTTP_422_UNPROCESSABLE_ENTITY
    default_code = "llm_content_blocked"
    default_detail = "The AI couldn't generate this because of its content policy. Try a different description."


class LLMInvalidResponseError(LLMError):
    default_code = "llm_invalid_response"
    default_detail = "The AI returned an incomplete design. Please try again."
    retriable = True


class SchemaValidationError(ApiError):
    """A user-supplied change (e.g. an edit patch) would make the schema invalid."""
    status_code = http.HTTP_400_BAD_REQUEST
    default_code = "invalid_schema"
    default_detail = "This change couldn't be applied because it would break the page structure."


# ---------------------------------------------------------------------------
# Scrubbing for logs
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    (re.compile(r"([?&]key=)[^&\s\"']+"), r"\1[REDACTED]"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{20,}"), "[REDACTED]"),
    (re.compile(r"gsk_[0-9A-Za-z]{10,}"), "[REDACTED]"),
    (re.compile(r"(Bearer\s+)[^\s\"']+", re.I), r"\1[REDACTED]"),
]


def scrub(text: Any, limit: int = 4000) -> str:
    """Remove API keys from text bound for logs, and cap its length."""
    text = str(text)
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text[:limit]


# ---------------------------------------------------------------------------
# Provider response -> typed error
# ---------------------------------------------------------------------------

def _json(response) -> dict:
    try:
        data = response.json()
        return data if isinstance(data, dict) else {}
    except (ValueError, json.JSONDecodeError):
        return {}


def _retry_after_seconds(response, body: dict) -> Optional[float]:
    header = (getattr(response, "headers", None) or {}).get("retry-after") or \
             (getattr(response, "headers", None) or {}).get("Retry-After")
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    # Gemini: error.details[] includes google.rpc.RetryInfo {"retryDelay": "12s"}
    for detail in (body.get("error") or {}).get("details") or []:
        delay = isinstance(detail, dict) and detail.get("retryDelay")
        if isinstance(delay, str) and delay.endswith("s"):
            try:
                return float(delay[:-1])
            except ValueError:
                pass
    # Groq: "Please try again in 7.66s" / "in 1m2.5s"
    message = str((body.get("error") or {}).get("message", ""))
    m = re.search(r"try again in (?:(\d+)m)?([\d.]+)s", message)
    if m:
        return int(m.group(1) or 0) * 60 + float(m.group(2))
    return None


def _quota_exhausted(text: str) -> bool:
    text = text.lower()
    return any(k in text for k in ("perday", "per day", "daily", "billing", "check your plan", "limit: 0"))


def error_from_response(provider: str, response) -> LLMError:
    """Map a non-2xx provider response to a typed error, logging the raw body."""
    status = getattr(response, "status_code", 0) or 0
    body = _json(response)
    raw = getattr(response, "text", "") or ""
    logger.error("%s API error: status=%s body=%s", provider, status, scrub(raw))

    err = body.get("error") if isinstance(body.get("error"), dict) else {}
    g_status = str(err.get("status", "")).upper()          # Gemini (google.rpc)
    o_type = str(err.get("type", "") or err.get("code", "")).lower()  # Groq / OpenAI style
    text = json.dumps(err) if err else raw

    if "API_KEY_INVALID" in text or "api key not valid" in text.lower() or "invalid_api_key" in o_type:
        return LLMQuotaError()
    if g_status in ("PERMISSION_DENIED", "UNAUTHENTICATED", "FAILED_PRECONDITION") or status in (401, 403):
        return LLMQuotaError()
    if g_status == "RESOURCE_EXHAUSTED" or status == 429:
        retry_after = _retry_after_seconds(response, body)
        if retry_after is None and _quota_exhausted(text):
            return LLMQuotaError()
        return LLMRateLimitError(retry_after=retry_after)
    if g_status == "DEADLINE_EXCEEDED" or status in (408, 504):
        return LLMTimeoutError()
    if g_status == "NOT_FOUND" or status == 404 or "model_not_found" in o_type or "model_decommissioned" in o_type:
        return LLMUnavailableError("This model is temporarily unavailable. Please choose a different model.")
    if g_status in ("UNAVAILABLE", "INTERNAL", "ABORTED") or status in (500, 502, 503, 498) or status >= 500:
        return LLMUnavailableError()
    if g_status == "INVALID_ARGUMENT" or status in (400, 413, 422):
        return LLMBadRequestError()
    return LLMError()


BLOCKED_FINISH_REASONS = {"SAFETY", "RECITATION", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "IMAGE_SAFETY"}


def gemini_text(data: dict) -> str:
    """The text of a successful Gemini response, or a typed error."""
    feedback = data.get("promptFeedback") or {}
    if feedback.get("blockReason"):
        logger.warning("Gemini blocked the prompt: %s", scrub(json.dumps(feedback)))
        raise LLMContentBlockedError()
    candidates = data.get("candidates") or []
    if not candidates:
        logger.error("Gemini returned no candidates: %s", scrub(json.dumps(data)))
        raise LLMInvalidResponseError()
    candidate = candidates[0] or {}
    reason = str(candidate.get("finishReason", "")).upper()
    if reason in BLOCKED_FINISH_REASONS:
        logger.warning("Gemini stopped generation: finishReason=%s safety=%s", reason, scrub(json.dumps(candidate.get("safetyRatings", []))))
        raise LLMContentBlockedError()
    try:
        parts = candidate["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    except (KeyError, TypeError):
        text = ""
    if not text.strip():
        logger.error("Gemini returned an empty answer: finishReason=%s", reason)
        raise LLMInvalidResponseError()
    return text


def groq_text(data: dict) -> str:
    """The text of a successful Groq (OpenAI-style) response, or a typed error."""
    try:
        choice = data["choices"][0]
        reason = str(choice.get("finish_reason", "")).lower()
        if reason == "content_filter":
            logger.warning("Groq content filter stopped generation")
            raise LLMContentBlockedError()
        text = choice["message"]["content"]
    except (KeyError, IndexError, TypeError):
        logger.error("Groq returned an unexpected payload: %s", scrub(json.dumps(data)[:2000]))
        raise LLMInvalidResponseError()
    if not text or not str(text).strip():
        raise LLMInvalidResponseError()
    return text


@contextlib.contextmanager
def provider_call(provider: str):
    """Turn transport failures into typed errors (and log them scrubbed)."""
    try:
        yield
    except LLMError:
        raise
    except requests.exceptions.Timeout as e:
        logger.error("%s request timed out: %s", provider, scrub(e))
        raise LLMTimeoutError() from None
    except requests.exceptions.RequestException as e:
        logger.error("%s request failed: %s", provider, scrub(e))
        raise LLMUnavailableError() from None
