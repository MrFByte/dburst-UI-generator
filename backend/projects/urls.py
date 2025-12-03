from django.urls import path
from .views import CreateProject, ListRecentProjects

urlpatterns = [
    path("create-project/", CreateProject.as_view(), name="create-project"),
    path("recent-projects/", ListRecentProjects.as_view(), name="recent-projects")
]
