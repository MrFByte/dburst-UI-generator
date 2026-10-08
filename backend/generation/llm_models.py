"""
Central registry for selectable AI models, sourced entirely from settings
(which in turn reads them from .env — see GROQ_UI_MODELS / GEMINI_UI_MODELS
and friends in config/settings.py). Swapping a deprecated model for a new
one is an .env edit, not a code change.

A model is identified end-to-end (frontend → API → LLMClient) by a single
composite id string: "<provider>:<model>", e.g. "groq:openai/gpt-oss-20b"
or "gemini:models/gemini-3.8-flash". This avoids guessing a model's
provider from its name (fragile — e.g. Gemini's "models/" prefix is just
Google's own URL convention, not a reliable signal).
"""
from django.conf import settings

PROVIDERS = {
    "groq": {
        "ui_models": settings.GROQ_UI_MODELS,
        "reasoning_model": settings.GROQ_REASONING_MODEL,
    },
    "gemini": {
        "ui_models": settings.GEMINI_UI_MODELS,
        "reasoning_model": settings.GEMINI_REASONING_MODEL,
    },
}

DEFAULT_UI_MODEL = settings.DEFAULT_UI_MODEL


def make_model_id(provider: str, model: str) -> str:
    return f"{provider}:{model}"


def parse_model_id(model_id: str):
    """Returns (provider, model) for a "provider:model" id.

    Raises ValueError if the id is malformed or the model isn't currently
    configured as available for that provider.
    """
    provider, _, model = model_id.partition(":")
    if not model or provider not in PROVIDERS or model not in PROVIDERS[provider]["ui_models"]:
        raise ValueError(f"Unknown model id: {model_id!r}")
    return provider, model


def is_valid_model_id(model_id: str) -> bool:
    try:
        parse_model_id(model_id)
        return True
    except ValueError:
        return False


def reasoning_model_for(provider: str) -> str:
    """The planner-stage model to pair with a UI model from this provider."""
    return PROVIDERS[provider]["reasoning_model"]


_ACRONYMS = {"gpt", "oss", "ui", "ai"}


def humanize(model: str) -> str:
    """Best-effort human label from a raw model id.

    e.g. "openai/gpt-oss-20b" -> "GPT OSS 20B", "models/gemini-3.8-flash"
    -> "Gemini 3.8 Flash". No metadata table to keep in sync — a model
    added to .env always gets a reasonable label for free.
    """
    name = model.rsplit("/", 1)[-1]
    words = []
    for token in name.split("-"):
        if not token:
            continue
        if token.lower() in _ACRONYMS:
            words.append(token.upper())
        elif token[:-1].isdigit() and token[-1].isalpha():
            words.append(token[:-1] + token[-1].upper())
        else:
            words.append(token.capitalize())
    return " ".join(words)


def available_models():
    """Flat list of {id, provider, model, label} for the frontend's picker."""
    models = []
    for provider, cfg in PROVIDERS.items():
        for model in cfg["ui_models"]:
            models.append({
                "id": make_model_id(provider, model),
                "provider": provider,
                "model": model,
                "label": humanize(model),
            })
    return models
