from django.urls import path
from .views import CreateProject, ListRecentProjects, ListAllProjects, GetProjectDetail

urlpatterns = [
    path("create-project/", CreateProject.as_view(), name="create-project"),
    path("recent-projects/", ListRecentProjects.as_view(), name="recent-projects"),
    path("all-projects/", ListAllProjects.as_view(), name="all-projects"),
    path("<uuid:project_id>/", GetProjectDetail.as_view(), name="project-detail"),
]
