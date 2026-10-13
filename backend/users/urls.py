from django.urls import path
from .views import (
    CSRFTokenView, GoogleAuthView, GithubAuthView, OAuthStartView,
    TokenRefreshView, LogoutView, ProfileView
)
from .session_views import (
    SessionAnalyticsView, CacheStatsView, ClearUserSessionsView
)

# Everything under auth/ receives the path-scoped refresh and OAuth-state
# cookies (settings.AUTH_REFRESH_COOKIE_PATH) — keep refresh/logout/callbacks here.
urlpatterns = [
    path("auth/csrf/", CSRFTokenView.as_view(), name="csrf-token"),
    path("auth/oauth/start/", OAuthStartView.as_view(), name="oauth-start"),
    path("auth/google/", GoogleAuthView.as_view(), name="google-auth"),
    path("auth/github/", GithubAuthView.as_view(), name="github-auth"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", ProfileView.as_view(), name="user-profile"),
    
    # Session management endpoints
    path("sessions/analytics/", SessionAnalyticsView.as_view(), name="session-analytics"),
    path("cache/stats/", CacheStatsView.as_view(), name="cache-stats"),
    path("sessions/clear/", ClearUserSessionsView.as_view(), name="clear-user-sessions"),
]
