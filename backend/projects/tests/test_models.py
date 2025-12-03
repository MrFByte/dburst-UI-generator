import pytest
from projects.models import Project
from users.models import User


@pytest.mark.django_db
def test_project_creation(user):
    """A project should be successfully created with a user owner."""
    project = Project.objects.create(
        user=user,
        title="My First Project",
        description="This is a test project",
        is_public=True,
    )

    assert project.id is not None
    assert project.user == user
    assert project.title == "My First Project"
    assert project.description == "This is a test project"
    assert project.is_public is True

    assert project.created_at is not None
    assert project.updated_at is not None


@pytest.mark.django_db
def test_project_default_values(user):
    """Check default behavior such as is_public=False."""
    project = Project.objects.create(
        user=user,
        title="Untitled Project",
    )

    assert project.description == "" 
    assert project.is_public is False


@pytest.mark.django_db
def test_project_str_method(user):
    """__str__ should return project title."""
    project = Project.objects.create(
        user=user,
        title="Dashboard Builder"
    )

    assert str(project) == "Dashboard Builder"


@pytest.mark.django_db
def test_project_belongs_to_user(user):
    """Project should attach correctly to the related_name 'projects'."""
    Project.objects.create(user=user, title="P1")
    Project.objects.create(user=user, title="P2")

    assert user.projects.count() == 2
    assert list(user.projects.values_list("title", flat=True)) == ["P1", "P2"]
