from django.urls import path
from .views import (
    StorePatchView,
    GetSchemaView,
    ListPatchesView,
    ClearCacheView,
)
from .version_views import GetVersionView, UndoView

urlpatterns = [
    path('<uuid:generation_id>/patch/', StorePatchView.as_view(), name='store-patch'),
    path('<uuid:generation_id>/schema/', GetSchemaView.as_view(), name='get-schema'),
    path('<uuid:generation_id>/patches/', ListPatchesView.as_view(), name='list-patches'),
    path('<uuid:generation_id>/cache/', ClearCacheView.as_view(), name='clear-cache'),
    
    # Version control endpoints
    path('<uuid:generation_id>/version/<uuid:patch_id>/', GetVersionView.as_view(), name='get-version'),
    path('<uuid:generation_id>/undo/', UndoView.as_view(), name='undo-patch'),
]
