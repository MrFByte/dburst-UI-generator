"""
Django management command to clean up expired sessions.

Usage:
    python manage.py cleanup_sessions
    python manage.py cleanup_sessions --analytics
"""

from django.core.management.base import BaseCommand
from users.session_manager import SessionManager, get_cache_stats
import json


class Command(BaseCommand):
    help = 'Clean up expired sessions and display session analytics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analytics',
            action='store_true',
            help='Display session analytics without cleanup',
        )
        parser.add_argument(
            '--cache-stats',
            action='store_true',
            help='Display Redis cache statistics',
        )

    def handle(self, *args, **options):
        if options['analytics']:
            self.display_analytics()
        elif options['cache_stats']:
            self.display_cache_stats()
        else:
            self.cleanup_sessions()

    def cleanup_sessions(self):
        """Perform session cleanup"""
        self.stdout.write(self.style.WARNING('Starting session cleanup...'))
        
        # Get initial count
        initial_count = SessionManager.get_active_session_count()
        self.stdout.write(f'Active sessions before cleanup: {initial_count}')
        
        # Perform cleanup
        cleared = SessionManager.clear_expired_sessions()
        
        # Get final count
        final_count = SessionManager.get_active_session_count()
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Session cleanup complete!'
        ))
        self.stdout.write(f'  - Sessions cleared: {cleared}')
        self.stdout.write(f'  - Active sessions: {final_count}')

    def display_analytics(self):
        """Display session analytics"""
        self.stdout.write(self.style.WARNING('Fetching session analytics...'))
        
        analytics = SessionManager.get_session_analytics()
        
        self.stdout.write(self.style.SUCCESS('\n📊 Session Analytics:'))
        self.stdout.write(f'  - Total sessions: {analytics.get("total_sessions", 0)}')
        self.stdout.write(f'  - Expiring within 24h: {analytics.get("expiring_within_24h", 0)}')
        self.stdout.write(f'  - Expiring after 24h: {analytics.get("expiring_after_24h", 0)}')
        self.stdout.write(f'  - Redis memory used: {analytics.get("redis_memory_used", "N/A")}')
        self.stdout.write(f'  - Timestamp: {analytics.get("timestamp", "N/A")}')

    def display_cache_stats(self):
        """Display Redis cache statistics"""
        self.stdout.write(self.style.WARNING('Fetching cache statistics...'))
        
        stats = get_cache_stats()
        
        if 'error' in stats:
            self.stdout.write(self.style.ERROR(f'Error: {stats["error"]}'))
            return
        
        self.stdout.write(self.style.SUCCESS('\n📈 Redis Cache Statistics:'))
        self.stdout.write(f'  - Redis version: {stats.get("redis_version", "N/A")}')
        self.stdout.write(f'  - Connected clients: {stats.get("connected_clients", 0)}')
        self.stdout.write(f'  - Memory used: {stats.get("used_memory_human", "N/A")}')
        self.stdout.write(f'  - Peak memory: {stats.get("used_memory_peak_human", "N/A")}')
        self.stdout.write(f'  - Commands processed: {stats.get("total_commands_processed", 0)}')
        self.stdout.write(f'  - Cache hit rate: {stats.get("hit_rate", "0%")}')
