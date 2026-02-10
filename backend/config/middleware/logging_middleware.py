"""
Logging Middleware

Automatically logs all HTTP requests and responses with timing information.
Provides visibility into API usage, performance, and errors.
"""

import time
import structlog
from django.utils.deprecation import MiddlewareMixin

logger = structlog.get_logger(__name__)


class LoggingMiddleware(MiddlewareMixin):
    """
    Log all HTTP requests and responses with timing and context.
    
    This middleware:
    - Logs when a request starts with method, path, and user info
    - Logs when a request completes with status code and duration
    - Includes timing information for performance monitoring
    - Adds user context for better debugging
    """
    
    def process_request(self, request):
        """Log request start and capture start time."""
        request.start_time = time.time()
        
        logger.info(
            "request_started",
            method=request.method,
            path=request.path,
            user=str(request.user.id) if request.user.is_authenticated else "anonymous",
            remote_addr=self._get_client_ip(request),
        )
    
    def process_response(self, request, response):
        """Log request completion with status and duration."""
        duration = time.time() - request.start_time if hasattr(request, 'start_time') else 0
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_func = logger.error
            event_name = "request_failed"
        elif response.status_code >= 400:
            log_func = logger.warning
            event_name = "request_error"
        else:
            log_func = logger.info
            event_name = "request_completed"
        
        log_func(
            event_name,
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            user=str(request.user.id) if request.user.is_authenticated else "anonymous",
            content_type=response.get('Content-Type', 'unknown'),
        )
        
        return response
    
    def process_exception(self, request, exception):
        """Log uncaught exceptions."""
        logger.error(
            "request_exception",
            method=request.method,
            path=request.path,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            user=str(request.user.id) if request.user.is_authenticated else "anonymous",
            exc_info=True,
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
