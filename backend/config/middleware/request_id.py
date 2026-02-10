"""
Request ID Middleware

Adds a unique request ID to each incoming request for tracing across logs.
The request ID is added to the structlog context and included in response headers.
"""

import uuid
import structlog
from django.utils.deprecation import MiddlewareMixin


class RequestIdMiddleware(MiddlewareMixin):
    """
    Add unique request ID to logs and response headers.
    
    This middleware:
    - Generates a unique UUID for each request
    - Binds it to the structlog context so all logs include it
    - Adds it to the response headers as 'X-Request-ID'
    - Enables request tracing across the entire system
    """
    
    def process_request(self, request):
        """Generate and bind request ID at the start of each request."""
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        
        # Clear any previous context and bind the new request ID
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
    def process_response(self, request, response):
        """Add request ID to response headers."""
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        return response
