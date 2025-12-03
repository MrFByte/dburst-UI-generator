import pytest
from projects.models import Project
from projects.serializers import ProjectSerializer


def test_project_serializer_fields():
    """Ensure serializer exposes the expected fields."""
    serializer = ProjectSerializer()

    expected_fields = {
        "id",
        "title",
        "description",
        "is_public",
        "created_at",
        "updated_at",
    }

    assert set(serializer.fields.keys()) == expected_fields


def test_project_serializer_requires_title():
    """Serializer should require the 'title' field."""
    serializer = ProjectSerializer(data={})

    assert not serializer.is_valid()
    assert "title" in serializer.errors


@pytest.mark.django_db
def test_project_serializer_output(user):
    """Serializer should output correct data from a model instance."""
    project = Project.objects.create(
        user=user,
        title="My Project",
        description="Test description",
        is_public=True
    )

    serializer = ProjectSerializer(project)
    data = serializer.data

    assert data["id"] == str(project.id)
    assert data["title"] == "My Project"
    assert data["description"] == "Test description"
    assert data["is_public"] is True

    assert data["created_at"] is not None
    assert data["updated_at"] is not None


@pytest.mark.django_db
def test_project_serializer_create(user):
    """Serializer should create a Project instance correctly."""

    payload = {
        "title": "New Serialized Project",
        "description": "Some text",
        "is_public": False
    }

    serializer = ProjectSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors

    project = serializer.save(user=user)

    assert project.title == payload["title"]
    assert project.description == payload["description"]
    assert project.is_public is False
    assert project.user == user


@pytest.mark.django_db
def test_project_serializer_update(user):
    """Serializer update should modify an existing project."""
    project = Project.objects.create(
        user=user,
        title="Old Title",
        description="Old desc"
    )

    payload = {
        "title": "Updated Title",
        "description": "Updated desc",
        "is_public": True
    }

    serializer = ProjectSerializer(instance=project, data=payload)
    assert serializer.is_valid(), serializer.errors

    updated = serializer.save()

    assert updated.title == "Updated Title"
    assert updated.description == "Updated desc"
    assert updated.is_public is True
