import pytest

from generation import llm_models


def test_available_models_includes_both_providers():
    models = llm_models.available_models()
    providers = {m["provider"] for m in models}
    assert providers == {"groq", "gemini"}


def test_available_models_ids_round_trip():
    """Every id returned by available_models() must parse back cleanly."""
    for m in llm_models.available_models():
        provider, model = llm_models.parse_model_id(m["id"])
        assert provider == m["provider"]
        assert model == m["model"]


def test_parse_model_id_rejects_unknown_model():
    with pytest.raises(ValueError):
        llm_models.parse_model_id("groq:some-deprecated-model")


def test_parse_model_id_rejects_unknown_provider():
    with pytest.raises(ValueError):
        llm_models.parse_model_id("openai:gpt-4")


def test_parse_model_id_rejects_missing_colon():
    with pytest.raises(ValueError):
        llm_models.parse_model_id("groq-openai-gpt-oss-20b")


def test_is_valid_model_id():
    assert llm_models.is_valid_model_id("groq:openai/gpt-oss-20b")
    assert not llm_models.is_valid_model_id("groq:nonexistent")


def test_reasoning_model_matches_provider():
    """The reasoning model for a provider must itself be from that provider's registry intent."""
    groq_reasoning = llm_models.reasoning_model_for("groq")
    gemini_reasoning = llm_models.reasoning_model_for("gemini")

    assert groq_reasoning == llm_models.PROVIDERS["groq"]["reasoning_model"]
    assert gemini_reasoning == llm_models.PROVIDERS["gemini"]["reasoning_model"]


def test_make_model_id_and_parse_are_inverse():
    model_id = llm_models.make_model_id("gemini", "models/gemini-3.5-flash")
    assert model_id == "gemini:models/gemini-3.5-flash"
    assert llm_models.parse_model_id(model_id) == ("gemini", "models/gemini-3.5-flash")


@pytest.mark.parametrize("model,expected", [
    ("openai/gpt-oss-20b", "GPT OSS 20B"),
    ("openai/gpt-oss-120b", "GPT OSS 120B"),
    ("models/gemini-3.8-flash", "Gemini 3.8 Flash"),
    ("models/gemini-3.5-flash-lite", "Gemini 3.5 Flash Lite"),
])
def test_humanize_labels(model, expected):
    assert llm_models.humanize(model) == expected
