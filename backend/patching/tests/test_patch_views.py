import pytest
import json
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from generation.models import Generations
from projects.models import Project
from patching.models import Patch
from generation.cache import GenerationCache

User = get_user_model()


@pytest.fixture
def api_client():
    """API client for making requests"""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user"""
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        name="Test User"
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """API client with authenticated user"""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def project(user):
    """Create a test project"""
    return Project.objects.create(
        user=user,
        title="Test Project",
        description="Test project description"
    )


@pytest.fixture
def generation(project):
    """Create a test generation"""
    schema = {
        "type": "Root",
        "props": {"className": "p-4"},
        "children": [
            {"type": "Text", "content": "Hello World"}
        ]
    }
    
    return Generations.objects.create(
        project=project,
        prompt="Create a test UI",
        schema=schema,
        llm_provider="groq",
        token_usage=100,
        status=Generations.Status.SUCCESS,
        metadata={"code": "const App = () => <div>Hello</div>"}
    )


@pytest.fixture
def cached_generation(generation):
    """Create a generation with cached data"""
    GenerationCache.store_generation(
        str(generation.id),
        generation.schema,
        "const App = () => <div>Hello</div>",
        {"provider": "groq", "usage": {"total_tokens": 100}}
    )
    return generation


class TestStorePatchView:
    """Test POST /api/v1/patching/<generation_id>/patch/"""
    
    def test_store_patch_success(self, authenticated_client, cached_generation):
        """Test successful patch application"""
        patch_data = {
            "patch": [
                {"op": "replace", "path": "/props/className", "value": "p-10"}
            ],
            "description": "Changed padding"
        }
        
        url = f"/api/v1/patching/{cached_generation.id}/patch/"
        response = authenticated_client.post(url, patch_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["generation_id"] == str(cached_generation.id)
        assert response.data["patch_count"] == 1
        assert response.data["snapshot_created"] is False
        
        # Verify patch stored in database
        assert Patch.objects.filter(generation=cached_generation).count() == 1
    
    def test_store_patch_unauthorized(self, api_client, cached_generation):
        """Test patch application without authentication"""
        patch_data = {
            "patch": [{"op": "replace", "path": "/props/className", "value": "p-10"}]
        }
        
        url = f"/api/v1/patching/{cached_generation.id}/patch/"
        response = api_client.post(url, patch_data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_store_patch_wrong_user(self, authenticated_client, cached_generation, db):
        """Test patch application by non-owner"""
        # Create another user
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123"
        )
        authenticated_client.force_authenticate(user=other_user)
        
        patch_data = {
            "patch": [{"op": "replace", "path": "/props/className", "value": "p-10"}]
        }
        
        url = f"/api/v1/patching/{cached_generation.id}/patch/"
        response = authenticated_client.post(url, patch_data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_store_patch_invalid_format(self, authenticated_client, cached_generation):
        """Test patch with invalid format"""
        patch_data = {
            "patch": "not a list"  # Should be a list
        }
        
        url = f"/api/v1/patching/{cached_generation.id}/patch/"
        response = authenticated_client.post(url, patch_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_store_patch_invalid_operation(self, authenticated_client, cached_generation):
        """Test patch with invalid operation"""
        patch_data = {
            "patch": [
                {"op": "invalid_op", "path": "/props/className", "value": "p-10"}
            ]
        }
        
        url = f"/api/v1/patching/{cached_generation.id}/patch/"
        response = authenticated_client.post(url, patch_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_store_patch_creates_snapshot_at_threshold(self, authenticated_client, cached_generation):
        """Test snapshot creation at 10th patch"""
        url = f"/api/v1/patching/{cached_generation.id}/patch/"
        
        # Apply 10 patches
        for i in range(10):
            patch_data = {
                "patch": [{"op": "replace", "path": "/props/className", "value": f"p-{i}"}],
                "description": f"Patch {i+1}"
            }
            response = authenticated_client.post(url, patch_data, format='json')
            assert response.status_code == status.HTTP_200_OK
        
        # 10th patch should create snapshot
        last_response = response
        assert last_response.data["patch_count"] == 10
        assert last_response.data["snapshot_created"] is True
        
        # Verify snapshot flag in database
        last_patch = Patch.objects.filter(generation=cached_generation).order_by('-applied_at').first()
        assert last_patch.snapshot_created is True


class TestGetSchemaView:
    """Test GET /api/v1/patching/<generation_id>/schema/"""
    
    def test_get_schema_from_cache(self, authenticated_client, cached_generation):
        """Test retrieving schema from cache"""
        url = f"/api/v1/patching/{cached_generation.id}/schema/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["generation_id"] == str(cached_generation.id)
        assert response.data["cached"] is True
        assert "schema" in response.data
        assert response.data["schema"]["type"] == "Root"
    
    def test_get_schema_from_database(self, authenticated_client, generation):
        """Test retrieving schema from database when not cached"""
        url = f"/api/v1/patching/{generation.id}/schema/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["cached"] is False
        assert "schema" in response.data
    
    def test_get_schema_unauthorized(self, api_client, cached_generation):
        """Test schema retrieval without authentication"""
        url = f"/api/v1/patching/{cached_generation.id}/schema/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_schema_not_found(self, authenticated_client):
        """Test schema retrieval for non-existent generation"""
        url = "/api/v1/patching/00000000-0000-0000-0000-000000000000/schema/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestListPatchesView:
    """Test GET /api/v1/patching/<generation_id>/patches/"""
    
    def test_list_patches_empty(self, authenticated_client, cached_generation):
        """Test listing patches when none exist"""
        url = f"/api/v1/patching/{cached_generation.id}/patches/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_patches"] == 0
        assert len(response.data["patches"]) == 0
    
    def test_list_patches_with_data(self, authenticated_client, cached_generation, user):
        """Test listing patches with existing data"""
        # Create some patches
        for i in range(5):
            Patch.objects.create(
                generation=cached_generation,
                user=user,
                patch_data=[{"op": "replace", "path": "/props/className", "value": f"p-{i}"}],
                description=f"Patch {i+1}"
            )
        
        url = f"/api/v1/patching/{cached_generation.id}/patches/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_patches"] == 5
        assert len(response.data["patches"]) == 5
    
    def test_list_patches_pagination(self, authenticated_client, cached_generation, user):
        """Test patch listing with pagination"""
        # Create 25 patches
        for i in range(25):
            Patch.objects.create(
                generation=cached_generation,
                user=user,
                patch_data=[{"op": "replace", "path": "/props/className", "value": f"p-{i}"}]
            )
        
        # Get first page
        url = f"/api/v1/patching/{cached_generation.id}/patches/?limit=10&offset=0"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_patches"] == 25
        assert len(response.data["patches"]) == 10
        assert response.data["limit"] == 10
        assert response.data["offset"] == 0
        
        # Get second page
        url = f"/api/v1/patching/{cached_generation.id}/patches/?limit=10&offset=10"
        response = authenticated_client.get(url)
        
        assert len(response.data["patches"]) == 10
    
    def test_list_patches_unauthorized(self, api_client, cached_generation):
        """Test patch listing without authentication"""
        url = f"/api/v1/patching/{cached_generation.id}/patches/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestClearCacheView:
    """Test DELETE /api/v1/patching/<generation_id>/cache/"""
    
    def test_clear_cache_success(self, authenticated_client, cached_generation):
        """Test successful cache clearing"""
        url = f"/api/v1/patching/{cached_generation.id}/cache/"
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        
        # Verify cache is cleared
        cached_data = GenerationCache.get_generation(str(cached_generation.id))
        assert cached_data is None
    
    def test_clear_cache_unauthorized(self, api_client, cached_generation):
        """Test cache clearing without authentication"""
        url = f"/api/v1/patching/{cached_generation.id}/cache/"
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
