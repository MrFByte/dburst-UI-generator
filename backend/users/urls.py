from django.urls import path
from .views import GoogleAuthView, GithubAuthView, TokenRefreshView, LogoutView, GetProfileView

urlpatterns = [
    path("auth/google/", GoogleAuthView.as_view(), name="google-auth"),
    path("auth/github/", GithubAuthView.as_view(), name="github-auth"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("profile/", GetProfileView.as_view(), name="user-profile"),
]