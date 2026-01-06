"""
Session management utilities for DBurst.
Provides functions for session analytics, cleanup, and monitoring.
"""
import logging
from django.core.cache import cache
from django_redis import get_redis_connection
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage Redis-backed sessions"""
    
    @staticmethod
    def get_active_session_count() -> int:
        """
        Get count of active sessions in Redis.
        
        Returns:
            Number of active sessions
        """
        try:
            redis_conn = get_redis_connection("default")
            # Count keys matching session pattern
            session_keys = redis_conn.keys("dburst:django.contrib.sessions.cache*")
            return len(session_keys)
        except Exception as e:
            logger.error(f"Failed to get session count: {e}")
            return 0
    
    @staticmethod
    def get_session_info(session_key: str) -> Optional[Dict]:
        """
        Get information about a specific session.
        
        Args:
            session_key: Session key to look up
            
        Returns:
            Session data dictionary or None
        """
        try:
            cache_key = f"django.contrib.sessions.cache{session_key}"
            session_data = cache.get(cache_key)
            
            if session_data:
                return {
                    "session_key": session_key,
                    "data": session_data,
                    "exists": True
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get session info for {session_key}: {e}")
            return None
    
    @staticmethod
    def clear_expired_sessions() -> int:
        """
        Clear expired sessions from Redis.
        Redis handles TTL automatically, but this provides manual cleanup.
        
        Returns:
            Number of sessions cleared
        """
        try:
            redis_conn = get_redis_connection("default")
            
            # Get all session keys
            session_keys = redis_conn.keys("dburst:django.contrib.sessions.cache*")
            
            cleared = 0
            for key in session_keys:
                # Check TTL
                ttl = redis_conn.ttl(key)
                if ttl == -1:  # No expiration set
                    # Set expiration to 7 days
                    redis_conn.expire(key, 86400 * 7)
                    logger.info(f"Set expiration for session: {key}")
                elif ttl == -2:  # Key doesn't exist
                    cleared += 1
            
            logger.info(f"Session cleanup complete. Cleared {cleared} expired sessions.")
            return cleared
        except Exception as e:
            logger.error(f"Failed to clear expired sessions: {e}")
            return 0
    
    @staticmethod
    def get_session_analytics() -> Dict:
        """
        Get analytics about current sessions.
        
        Returns:
            Dictionary with session statistics
        """
        try:
            redis_conn = get_redis_connection("default")
            
            session_keys = redis_conn.keys("dburst:django.contrib.sessions.cache*")
            total_sessions = len(session_keys)
            
            # Get memory usage
            memory_info = redis_conn.info('memory')
            used_memory = memory_info.get('used_memory_human', 'N/A')
            
            # Calculate sessions by TTL
            expiring_soon = 0  # < 1 day
            expiring_later = 0  # > 1 day
            
            for key in session_keys:
                ttl = redis_conn.ttl(key)
                if 0 < ttl < 86400:  # Less than 1 day
                    expiring_soon += 1
                elif ttl >= 86400:
                    expiring_later += 1
            
            return {
                "total_sessions": total_sessions,
                "expiring_within_24h": expiring_soon,
                "expiring_after_24h": expiring_later,
                "redis_memory_used": used_memory,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get session analytics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @staticmethod
    def clear_user_sessions(user_id: str) -> int:
        """
        Clear all sessions for a specific user.
        Useful for logout from all devices.
        
        Args:
            user_id: User ID to clear sessions for
            
        Returns:
            Number of sessions cleared
        """
        try:
            redis_conn = get_redis_connection("default")
            
            # Get all session keys
            session_keys = redis_conn.keys("dburst:django.contrib.sessions.cache*")
            
            cleared = 0
            for key in session_keys:
                try:
                    # Get session data
                    session_data = cache.get(key.decode().replace("dburst:", ""))
                    if session_data and session_data.get('_auth_user_id') == user_id:
                        redis_conn.delete(key)
                        cleared += 1
                except Exception:
                    continue
            
            logger.info(f"Cleared {cleared} sessions for user {user_id}")
            return cleared
        except Exception as e:
            logger.error(f"Failed to clear user sessions: {e}")
            return 0


def get_cache_stats() -> Dict:
    """
    Get Redis cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    try:
        redis_conn = get_redis_connection("default")
        info = redis_conn.info()
        
        return {
            "redis_version": info.get('redis_version'),
            "connected_clients": info.get('connected_clients'),
            "used_memory_human": info.get('used_memory_human'),
            "used_memory_peak_human": info.get('used_memory_peak_human'),
            "total_commands_processed": info.get('total_commands_processed'),
            "keyspace_hits": info.get('keyspace_hits', 0),
            "keyspace_misses": info.get('keyspace_misses', 0),
            "hit_rate": calculate_hit_rate(
                info.get('keyspace_hits', 0),
                info.get('keyspace_misses', 0)
            ),
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"error": str(e)}


def calculate_hit_rate(hits: int, misses: int) -> str:
    """Calculate cache hit rate percentage"""
    total = hits + misses
    if total == 0:
        return "0%"
    return f"{(hits / total * 100):.2f}%"
