"""
Resolves real, working photo URLs for every Image node in a generated UI
schema. The UI-generator LLM has no vision or web access, so it cannot know
a real Unsplash photo id — asking it to produce "src" directly just gets a
hallucinated, 404ing URL. Instead it writes a descriptive "alt" text per
Image node (see UI_GENERATOR_SYSTEM_PROMPT in llm.py), and this module turns
that text into a real photo via the Unsplash Search API, falling back to a
deterministic Picsum placeholder whenever Unsplash is unavailable, rate
limited, unconfigured, or returns nothing.
"""
import logging
import re
import requests
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

UNSPLASH_SEARCH_URL = "https://api.unsplash.com/search/photos"
REQUEST_TIMEOUT_SECONDS = 4
CACHE_KEY_PREFIX = "img:unsplash:"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "image"


def _placeholder_url(query: str, width: int = 800, height: int = 600) -> str:
    return f"https://picsum.photos/seed/{_slugify(query)}/{width}/{height}"


def _search_unsplash(query: str) -> Optional[str]:
    access_key = getattr(settings, "UNSPLASH_ACCESS_KEY", None)
    if not access_key:
        return None

    try:
        response = requests.get(
            UNSPLASH_SEARCH_URL,
            params={"query": query, "per_page": 1},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.warning(f"Unsplash search failed ({response.status_code}) for query={query!r}")
            return None

        results = response.json().get("results", [])
        if not results:
            return None

        url = results[0]["urls"]["regular"]
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}utm_source=dburst&utm_medium=referral"
    except Exception as e:
        logger.warning(f"Unsplash search errored for query={query!r}: {e}")
        return None


def _resolve_query(query: str, calls_made: int, max_calls: int) -> tuple[str, int]:
    """Returns (url, updated_calls_made)."""
    normalized = query.strip().lower()
    cache_key = f"{CACHE_KEY_PREFIX}{_slugify(normalized)}"

    cached_url = cache.get(cache_key)
    if cached_url:
        return cached_url, calls_made

    if calls_made >= max_calls:
        return _placeholder_url(query), calls_made

    url = _search_unsplash(query)
    calls_made += 1

    if not url:
        url = _placeholder_url(query)
    else:
        ttl = getattr(settings, "IMAGE_CACHE_TTL_SECONDS", 604800)
        cache.set(cache_key, url, ttl)

    return url, calls_made


def resolve_schema_images(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Walks the schema tree and sets a real/placeholder "src" on every
    Image node, resolved from that node's "alt" text. Never raises —
    any node that can't be resolved gets a placeholder instead.
    """
    max_calls = getattr(settings, "UNSPLASH_MAX_CALLS_PER_GENERATION", 10)
    state = {"calls_made": 0, "resolved": {}}

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "Image":
                props = node.setdefault("props", {})
                query = (props.get("alt") or "abstract background").strip() or "abstract background"

                if query not in state["resolved"]:
                    try:
                        url, state["calls_made"] = _resolve_query(query, state["calls_made"], max_calls)
                    except Exception as e:
                        logger.warning(f"Image resolution failed for query={query!r}: {e}")
                        url = _placeholder_url(query)
                    state["resolved"][query] = url

                props["src"] = state["resolved"][query]

            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    try:
        walk(schema)
    except Exception as e:
        logger.error(f"resolve_schema_images failed unexpectedly, leaving schema untouched: {e}")

    return schema
