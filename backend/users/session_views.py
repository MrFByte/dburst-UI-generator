"""
Session monitoring and management API views.
"""

from config.api_errors import error_response
import logging
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .session_manager import SessionManager, get_cache_stats
from .services import clear_auth_cookies, revoke_access_token
from .views import blacklist_all_refresh_tokens

logger = logging.getLogger(__name__)


class SessionAnalyticsView(APIView):
    """
    Get session analytics (admin only).
    
    GET /api/v1/users/sessions/analytics/
    
    Response:
        {
            "total_sessions": 10,
            "expiring_within_24h": 2,
            "expiring_after_24h": 8,
            "redis_memory_used": "2.5M",
            "timestamp": "2026-01-05T10:30:00"
        }
    """
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        try:
            analytics = SessionManager.get_session_analytics()
            return Response(analytics, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Error getting session analytics: {e}")
            return error_response("Failed to retrieve session analytics", "server_error", 500)


class CacheStatsView(APIView):
    """
    Get Redis cache statistics (admin only).
    
    GET /api/v1/users/cache/stats/
    
    Response:
        {
            "redis_version": "7.0.0",
            "connected_clients": 5,
            "used_memory_human": "10M",
            "hit_rate": "85.5%"
        }
    """
    
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        try:
            stats = get_cache_stats()
            return Response(stats, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Error getting cache stats: {e}")
            return error_response("Failed to retrieve cache statistics", "server_error", 500)


class ClearUserSessionsView(APIView):
    """
    Log the authenticated user out of every device.

    Blacklists all of the requesting user's outstanding refresh tokens (so no
    other browser can refresh), revokes the current access token, and clears
    this browser's cookies. Only ever touches request.user's own tokens.

    POST /api/v1/users/sessions/clear/

    Response:
        {
            "success": true,
            "sessions_cleared": 3,
            "message": "Cleared 3 session(s) successfully"
        }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cleared = blacklist_all_refresh_tokens(request.user)
        revoke_access_token(request.auth)

        response = Response({
            "success": True,
            "sessions_cleared": cleared,
            "message": f"Cleared {cleared} session(s) successfully"
        }, status=status.HTTP_200_OK)
        return clear_auth_cookies(response)
