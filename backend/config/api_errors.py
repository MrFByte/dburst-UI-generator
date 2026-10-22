"""
One error contract for every API error response:

    {
      "error": "<human message>",        # always present (clients read this)
      "code": "<stable_machine_code>",   # always present
      "details": {...},                  # optional, e.g. per-field errors
      "retry_after": 12,                 # optional seconds (429s)
      "request_id": "<uuid>"             # when available, for support
    }

Raise an ApiError (or a subclass) from a view and config.exception_handler
renders it; or return error_response(...) directly. Messages here are shown
to end users, so they must never carry exception text, provider payloads or
internals: log those instead.
"""
import math
from typing import Any, Optional

import structlog
from rest_framework import status as http
from rest_framework.exceptions import APIException
from rest_framework.response import Response

GENERIC_SERVER_ERROR = "Something went wrong on our side. Please try again."


def current_request_id() -> Optional[str]:
    """The id RequestIdMiddleware bound for this request, if any."""
    return structlog.contextvars.get_contextvars().get("request_id")


def error_body(message: str, code: str, details: Any = None, retry_after: Optional[float] = None) -> dict:
    body = {"error": message, "code": code}
    if details:
        body["details"] = details
    if retry_after is not None:
        body["retry_after"] = max(1, math.ceil(retry_after))
    request_id = current_request_id()
    if request_id:
        body["request_id"] = request_id
    return body


def error_response(
    message: str,
    code: str,
    status: int,
    details: Any = None,
    retry_after: Optional[float] = None,
) -> Response:
    """A contract-shaped error Response (with Retry-After when given)."""
    response = Response(error_body(message, code, details, retry_after), status=status)
    if retry_after is not None:
        response["Retry-After"] = str(max(1, math.ceil(retry_after)))
    return response


class ApiError(APIException):
    """Base for errors with a user-safe message and a stable code."""

    status_code = http.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = GENERIC_SERVER_ERROR
    default_code = "server_error"

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        code: Optional[str] = None,
        details: Any = None,
        retry_after: Optional[float] = None,
        status_code: Optional[int] = None,
    ):
        self.error_code = code or self.default_code
        self.message = message or self.default_detail
        self.details = details
        self.retry_after = retry_after
        if status_code is not None:
            self.status_code = status_code
        # DRF's default handler turns `wait` into a Retry-After header.
        self.wait = retry_after
        super().__init__(detail=self.message, code=self.error_code)
