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
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="integration@example.com",
        password="testpass123",
        name="Integration Test User"
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestFullGenerationToPatchFlow:
    """Test complete flow from generation to patch application"""
    
    def test_complete_workflow(self, authenticated_client, user):
        """
        Test the complete workflow:
        1. Create project
        2. Generate UI (mocked)
        3. Verify caching
        4. Apply patches
        5. Retrieve schema
        6. List patches
        7. Clear cache
        """
        
        # Step 1: Create a project manually
        project = Project.objects.create(
            user=user,
            title="Integration Test Project",
            description="Testing full workflow"
        )
        
        # Step 2: Create a generation (simulating GenerateView)
        schema = {
            "type": "Root",
            "props": {"className": "p-4 bg-white"},
            "children": [
                {
                    "type": "Section",
                    "props": {"className": "container mx-auto"},
                    "children": [
                        {"type": "Text", "content": "Welcome to DBurst"}
                    ]
                }
            ]
        }
        
        generation = Generations.objects.create(
            project=project,
            prompt="Create a landing page",
            schema=schema,
            llm_provider="groq",
            token_usage=150,
            status=Generations.Status.SUCCESS,
            metadata={
                "code": "const App = () => <div>Welcome</div>",
                "design_plan": {"concept": "Modern landing page"}
            }
        )
        
        # Step 3: Cache the generation
        GenerationCache.store_generation(
            str(generation.id),
            schema,
            "const App = () => <div>Welcome</div>",
            {"provider": "groq", "usage": {"total_tokens": 150}}
        )
        
        # Verify caching
        cached_data = GenerationCache.get_generation(str(generation.id))
        assert cached_data is not None
        assert cached_data["schema"]["type"] == "Root"
        
        # Step 4: Apply first patch (change background)
        patch_url = f"/api/v1/patching/{generation.id}/patch/"
        patch1 = {
            "patch": [
                {"op": "replace", "path": "/props/className", "value": "p-4 bg-gradient-to-br from-blue-50 to-purple-50"}
            ],
            "description": "Changed to gradient background"
        }
        
        response1 = authenticated_client.post(patch_url, patch1, format='json')
        assert response1.status_code == status.HTTP_200_OK
        assert response1.data["patch_count"] == 1
        assert response1.data["snapshot_created"] is False
        
        # Step 5: Apply second patch (change text)
        patch2 = {
            "patch": [
                {"op": "replace", "path": "/children/0/children/0/content", "value": "Welcome to DBurst AI Builder"}
            ],
            "description": "Updated welcome text"
        }
        
        response2 = authenticated_client.post(patch_url, patch2, format='json')
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data["patch_count"] == 2
        
        # Step 6: Retrieve current schema
        schema_url = f"/api/v1/patching/{generation.id}/schema/"
        schema_response = authenticated_client.get(schema_url)
        
        assert schema_response.status_code == status.HTTP_200_OK
        assert schema_response.data["cached"] is True
        assert schema_response.data["patch_count"] == 2
        
        # Verify schema has both patches applied
        updated_schema = schema_response.data["schema"]
        assert "gradient" in updated_schema["props"]["className"]
        assert updated_schema["children"][0]["children"][0]["content"] == "Welcome to DBurst AI Builder"
        
        # Step 7: List all patches
        patches_url = f"/api/v1/patching/{generation.id}/patches/"
        patches_response = authenticated_client.get(patches_url)
        
        assert patches_response.status_code == status.HTTP_200_OK
        assert patches_response.data["total_patches"] == 2
        assert len(patches_response.data["patches"]) == 2
        
        # Verify patch metadata
        patches = patches_response.data["patches"]
        assert patches[0]["description"] == "Updated welcome text"  # Newest first
        assert patches[1]["description"] == "Changed to gradient background"
        
        # Step 8: Clear cache
        cache_url = f"/api/v1/patching/{generation.id}/cache/"
        clear_response = authenticated_client.delete(cache_url)
        
        assert clear_response.status_code == status.HTTP_200_OK
        assert clear_response.data["success"] is True
        
        # Verify cache is cleared
        cached_data = GenerationCache.get_generation(str(generation.id))
        assert cached_data is None
        
        # Step 9: Schema should still be retrievable from database
        schema_response2 = authenticated_client.get(schema_url)
        assert schema_response2.status_code == status.HTTP_200_OK
        assert schema_response2.data["cached"] is False  # From database now


@pytest.mark.django_db
class TestSnapshotCreationFlow:
    """Test snapshot creation after 10 patches"""
    
    def test_snapshot_at_threshold(self, authenticated_client, user):
        """Test that snapshot is created at 10th patch and schema is persisted"""
        
        # Create project and generation
        project = Project.objects.create(user=user, title="Snapshot Test")
        
        initial_schema = {
            "type": "Root",
            "props": {"className": "p-4"},
            "children": []
        }
        
        generation = Generations.objects.create(
            project=project,
            prompt="Test snapshot",
            schema=initial_schema,
            llm_provider="groq",
            token_usage=100,
            status=Generations.Status.SUCCESS
        )
        
        # Cache the generation
        GenerationCache.store_generation(
            str(generation.id),
            initial_schema,
            "const App = () => <div></div>",
            {}
        )
        
        # Apply 10 patches
        patch_url = f"/api/v1/patching/{generation.id}/patch/"
        
        for i in range(10):
            patch_data = {
                "patch": [
                    {"op": "replace", "path": "/props/className", "value": f"p-{i+1}"}
                ],
                "description": f"Patch number {i+1}"
            }
            
            response = authenticated_client.post(patch_url, patch_data, format='json')
            assert response.status_code == status.HTTP_200_OK
            
            if i < 9:
                assert response.data["snapshot_created"] is False
            else:
                # 10th patch should create snapshot
                assert response.data["snapshot_created"] is True
        
        # Verify database was updated with latest schema
        generation.refresh_from_db()
        assert generation.schema["props"]["className"] == "p-10"
        
        # Verify snapshot flag in database
        snapshot_patches = Patch.objects.filter(
            generation=generation,
            snapshot_created=True
        )
        assert snapshot_patches.count() == 1


@pytest.mark.django_db
class TestMultipleUsersIsolation:
    """Test that users can only access their own generations"""
    
    def test_user_isolation(self, api_client, db):
        """Test that users cannot access other users' generations"""
        
        # Create two users
        user1 = User.objects.create_user(email="user1@test.com", password="pass123")
        user2 = User.objects.create_user(email="user2@test.com", password="pass123")
        
        # Create project and generation for user1
        project1 = Project.objects.create(user=user1, title="User1 Project")
        generation1 = Generations.objects.create(
            project=project1,
            prompt="User1 generation",
            schema={"type": "Root"},
            llm_provider="groq",
            token_usage=100,
            status=Generations.Status.SUCCESS
        )
        
        GenerationCache.store_generation(
            str(generation1.id),
            {"type": "Root"},
            "code",
            {}
        )
        
        # User2 tries to access user1's generation
        api_client.force_authenticate(user=user2)
        
        # Try to apply patch
        patch_url = f"/api/v1/patching/{generation1.id}/patch/"
        response = api_client.post(patch_url, {
            "patch": [{"op": "replace", "path": "/props/className", "value": "p-10"}]
        }, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Try to get schema
        schema_url = f"/api/v1/patching/{generation1.id}/schema/"
        response = api_client.get(schema_url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Try to list patches
        patches_url = f"/api/v1/patching/{generation1.id}/patches/"
        response = api_client.get(patches_url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestErrorRecovery:
    """Test error handling and recovery scenarios"""
    
    def test_patch_application_with_cache_miss(self, authenticated_client, user):
        """Test that patch application works even if cache is empty (loads from DB)"""
        
        project = Project.objects.create(user=user, title="Cache Miss Test")
        
        schema = {"type": "Root", "props": {"className": "p-4"}}
        
        generation = Generations.objects.create(
            project=project,
            prompt="Test",
            schema=schema,
            llm_provider="groq",
            token_usage=100,
            status=Generations.Status.SUCCESS,
            metadata={"code": "const App = () => <div></div>"}
        )
        
        # Don't cache the generation - simulate cache miss
        
        # Apply patch - should load from DB and then cache
        patch_url = f"/api/v1/patching/{generation.id}/patch/"
        response = authenticated_client.post(patch_url, {
            "patch": [{"op": "replace", "path": "/props/className", "value": "p-10"}],
            "description": "Test patch"
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        
        # Verify it's now cached
        cached_data = GenerationCache.get_generation(str(generation.id))
        assert cached_data is not None
        assert cached_data["schema"]["props"]["className"] == "p-10"
