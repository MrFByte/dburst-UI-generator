from django.urls import path
from .views import GenerateView, GenerationDetailView, AvailableModelsView
from .views_chat import get_chat_history, refine_ui

urlpatterns = [
    path("generate/", GenerateView.as_view(), name="generate"),
    path("models/", AvailableModelsView.as_view(), name="available-models"),
    path("details/<uuid:generation_id>/", GenerationDetailView.as_view(), name="generation-detail"),
    path("chat/history/<uuid:generation_id>/", get_chat_history, name="chat-history"),
    path("chat/refine/", refine_ui, name="refine-ui"),
]
