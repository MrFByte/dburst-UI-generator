import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404, JsonResponse
from rest_framework import exceptions as drf
from rest_framework import status as http
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from .api_errors import GENERIC_SERVER_ERROR, ApiError, error_body

logger = logging.getLogger("api.errors")

VALIDATION_MESSAGE = "Please check the highlighted fields and try again."

# Friendly wording for DRF's built-in exceptions. Their own detail strings are
# developer-facing ("JSON parse error - Expecting value: line 1 column 1").
DRF_ERRORS = {
    drf.NotAuthenticated: ("not_authenticated", "Please sign in to continue."),
    drf.AuthenticationFailed: ("not_authenticated", "Your session has expired. Please sign in again."),
    drf.PermissionDenied: ("permission_denied", "You don't have permission to do that."),
    drf.NotFound: ("not_found", "We couldn't find what you were looking for."),
    drf.MethodNotAllowed: ("method_not_allowed", "This action isn't supported."),
    drf.NotAcceptable: ("not_acceptable", "The server can't respond in the requested format."),
    drf.UnsupportedMediaType: ("unsupported_media_type", "This kind of upload isn't supported."),
    drf.ParseError: ("bad_request", "The request couldn't be read. Please refresh the page and try again."),
}
CSRF_MESSAGE = "Your session security check failed. Please refresh the page and try again."


def _flatten_messages(detail):
    """All messages in a DRF ValidationError detail (dict/list/str), in order."""
    if isinstance(detail, dict):
        for value in detail.values():
            yield from _flatten_messages(value)
    elif isinstance(detail, (list, tuple)):
        for value in detail:
            yield from _flatten_messages(value)
    elif detail is not None:
        yield str(detail)


def _validation_payload(exc: drf.ValidationError):
    detail = exc.detail
    if isinstance(detail, dict):
        details = {k: [str(m) for m in _flatten_messages(v)] for k, v in detail.items()}
    else:
        details = {"non_field_errors": [str(m) for m in _flatten_messages(detail)]}
    pairs = [(field, m) for field, msgs in details.items() for m in msgs]
    if len(pairs) != 1:
        return VALIDATION_MESSAGE, details
    # One problem: say it plainly. DRF's generic "This field ..." messages
    # get the field's name so they make sense outside the form.
    field, message = pairs[0]
    if message.startswith("This field") and field != "non_field_errors":
        message = field.replace("_", " ").capitalize() + message[len("This field"):]
    return message, details


def _classify(exc):
    """(status, code, message, details, retry_after) for a handled exception."""
    if isinstance(exc, ApiError):
        return exc.status_code, exc.error_code, exc.message, exc.details, exc.retry_after
    if isinstance(exc, drf.ValidationError):
        message, details = _validation_payload(exc)
        return http.HTTP_400_BAD_REQUEST, "validation_error", message, details, None
    if isinstance(exc, drf.Throttled):
        wait = exc.wait
        seconds = f"{int(wait) + (wait % 1 > 0)} seconds" if wait else "a moment"
        message = f"You're doing that too often. Please wait {seconds} and try again."
        return http.HTTP_429_TOO_MANY_REQUESTS, "throttled", message, None, wait
    if isinstance(exc, Http404):
        exc = drf.NotFound()
    if isinstance(exc, DjangoPermissionDenied):
        exc = drf.PermissionDenied()
    if isinstance(exc, drf.PermissionDenied) and str(exc.detail).startswith("CSRF Failed"):
        return http.HTTP_403_FORBIDDEN, "csrf_failed", CSRF_MESSAGE, None, None
    for cls, (code, message) in DRF_ERRORS.items():
        if isinstance(exc, cls):
            return exc.status_code, code, message, None, None
    if isinstance(exc, drf.APIException):
        return exc.status_code, "error", GENERIC_SERVER_ERROR, None, None
    return None


def api_exception_handler(exc, context):
    """Render every exception that reaches DRF in the API error contract.

    Raw details (exception text, provider payloads, CSRF reasons) go to the
    logs only. Unhandled exceptions are logged with their traceback and
    answered with a generic 500 that carries the request id.
    """
    request = context.get("request")
    view = context.get("view")
    where = f"{getattr(request, 'method', '?')} {getattr(request, 'path', '?')} (view={type(view).__name__ if view else '?'})"

    response = drf_exception_handler(exc, context)
    classified = _classify(exc)

    if response is None or classified is None:
        logger.error("Unhandled exception in %s", where, exc_info=(type(exc), exc, exc.__traceback__))
        response = Response(status=http.HTTP_500_INTERNAL_SERVER_ERROR)
        status, code, message, details, retry_after = (500, "server_error", GENERIC_SERVER_ERROR, None, None)
    else:
        status, code, message, details, retry_after = classified
        if isinstance(exc, drf.MethodNotAllowed) and view is not None:
            logger.warning("Method Not Allowed: %s (allowed=%s)", where, ", ".join(view.allowed_methods))
        elif code == "csrf_failed":
            logger.warning("CSRF rejected: %s: %s", where, exc.detail)
        elif status >= 500:
            logger.error("API error %s %s in %s: %s", status, code, where, exc)

    response.status_code = status
    response.data = error_body(message, code, details, retry_after)
    if retry_after:
        response["Retry-After"] = str(max(1, int(retry_after) + (retry_after % 1 > 0)))
    return response


def json_not_found(request, exception=None):
    """handler404: JSON for API paths instead of Django's HTML page."""
    return JsonResponse(error_body("We couldn't find what you were looking for.", "not_found"), status=404)


def json_server_error(request):
    """handler500: errors that escape DRF (middleware, non-DRF views)."""
    return JsonResponse(error_body(GENERIC_SERVER_ERROR, "server_error"), status=500)
