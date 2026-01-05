"""
Session monitoring and management API views.
"""

import logging
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .session_manager import SessionManager, get_cache_stats

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
            logger.error(f"Error getting session analytics: {e}")
            return Response(
                {"error": "Failed to retrieve session analytics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
            logger.error(f"Error getting cache stats: {e}")
            return Response(
                {"error": "Failed to retrieve cache statistics"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ClearUserSessionsView(APIView):
    """
    Clear all sessions for the authenticated user (logout from all devices).
    
    POST /api/v1/users/sessions/clear/
    
    Response:
        {
            "success": true,
            "sessions_cleared": 3,
            "message": "All sessions cleared successfully"
        }
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            user_id = str(request.user.id)
            cleared = SessionManager.clear_user_sessions(user_id)
            
            return Response({
                "success": True,
                "sessions_cleared": cleared,
                "message": f"Cleared {cleared} session(s) successfully"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error clearing user sessions: {e}")
            return Response(
                {"error": "Failed to clear sessions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
