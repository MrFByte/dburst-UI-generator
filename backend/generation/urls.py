from django.urls import path
from .views import GenerateView, GenerationDetailView

urlpatterns = [
    path("generate/", GenerateView.as_view(), name="generate"),
    path("details/<uuid:generation_id>/", GenerationDetailView.as_view(), name="generation-detail"),
]
