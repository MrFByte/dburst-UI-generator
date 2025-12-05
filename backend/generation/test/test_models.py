import pytest
from projects.models import Project
from generation.models import Generations


@pytest.fixture
def project(db, user):
    return Project.objects.create(
        user=user,
        title="Test Project",
        description="Desc"
    )


@pytest.mark.django_db
def test_generations_model_create(project):
    gen = Generations.objects.create(
        project=project,
        prompt="Generate a landing page",
        schema={"type": "Root", "children": []},
        llm_provider=Generations.Provider.GROQ,
        token_usage=500,
        status=Generations.Status.SUCCESS
    )

    assert gen.project == project
    assert gen.prompt == "Generate a landing page"
    assert gen.schema == {"type": "Root", "children": []}
    assert gen.llm_provider == "groq"
    assert gen.token_usage == 500
    assert gen.status == "success"
    assert gen.id is not None
    assert gen.created_at is not None


@pytest.mark.django_db
def test_generations_default_values(project):
    gen = Generations.objects.create(
        project=project,
        llm_provider=Generations.Provider.OPENAI,
    )

    assert gen.prompt == ""
    assert gen.schema == {}
    assert gen.code_bundle_url is None
    assert gen.token_usage == 0
    assert gen.status == Generations.Status.PENDING


@pytest.mark.django_db
def test_generations_provider_choices(project):
    gen = Generations.objects.create(
        project=project,
        llm_provider=Generations.Provider.GEMINI,
    )

    assert gen.llm_provider == "gemini"


@pytest.mark.django_db
def test_generations_status_choices(project):
    gen = Generations.objects.create(
        project=project,
        llm_provider=Generations.Provider.GROQ,
        status=Generations.Status.FAILED
    )

    assert gen.status == "failed"


@pytest.mark.django_db
def test_generations_str_output(project):
    gen = Generations.objects.create(
        project=project,
        llm_provider=Generations.Provider.GROQ,
        status=Generations.Status.SUCCESS
    )

    assert str(gen) == f"{project.title} → success"