from django.urls import path
from .views import CreateProject, ListRecentProjects

urlpatterns = [
    path("create-project/", CreateProject.as_view(), name="generate"),
    path("recent-projects/", ListRecentProjects.as_view(), name="recent_projects")
]
