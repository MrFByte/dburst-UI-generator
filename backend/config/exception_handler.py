import logging

from rest_framework.exceptions import MethodNotAllowed
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("api.errors")


def api_exception_handler(exc, context):
    """DRF's default handler, plus a diagnosable line for 405s.

    Django's own "Method Not Allowed: <path>" log line omits the method and
    the view, which makes a stale server or a wrong client call hard to tell
    apart. This logs both, along with what the view actually allows.
    """
    response = drf_exception_handler(exc, context)
    if isinstance(exc, MethodNotAllowed):
        request = context.get("request")
        view = context.get("view")
        logger.warning(
            "Method Not Allowed: %s %s (view=%s, allowed=%s)",
            getattr(request, "method", "?"),
            getattr(request, "path", "?"),
            type(view).__name__ if view else "?",
            ", ".join(view.allowed_methods) if view else "?",
        )
    return response
