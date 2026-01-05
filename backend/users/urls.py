from django.urls import path
from .views import (
    GoogleAuthView, GithubAuthView, TokenRefreshView, 
    LogoutView, GetProfileView
)
from .session_views import (
    SessionAnalyticsView, CacheStatsView, ClearUserSessionsView
)

urlpatterns = [
    path("auth/google/", GoogleAuthView.as_view(), name="google-auth"),
    path("auth/github/", GithubAuthView.as_view(), name="github-auth"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", GetProfileView.as_view(), name="user-profile"),
    
    # Session management endpoints
    path("sessions/analytics/", SessionAnalyticsView.as_view(), name="session-analytics"),
    path("cache/stats/", CacheStatsView.as_view(), name="cache-stats"),
    path("sessions/clear/", ClearUserSessionsView.as_view(), name="clear-user-sessions"),
]