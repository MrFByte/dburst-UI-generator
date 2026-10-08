"""
Resolves real, working photo URLs for every Image node in a generated UI
schema. The UI-generator LLM has no vision or web access, so it cannot know
a real photo id — asking it to produce "src" directly just gets a
hallucinated, 404ing URL. Instead it writes a descriptive "alt" text per
Image node (see UI_GENERATOR_SYSTEM_PROMPT in llm.py), and this module turns
that text into a real photo via the Pixabay Search API (free, instant API
key, no approval/review needed — see pixabay.com/api/docs), falling back to
a placehold.co placeholder whenever Pixabay is unavailable, rate limited,
unconfigured, or returns nothing.

The fallback deliberately isn't picsum.photos: picsum's seed URLs are a
302 redirect to a different origin (fastly.picsum.photos) with no
Cross-Origin-Resource-Policy header on that redirect response, which gets
blocked by COEP:credentialless inside any cross-origin-isolated context
(e.g. the WebContainer live-preview iframe) with
net::ERR_BLOCKED_BY_RESPONSE.NotSameOriginAfterDefaultedToSameOriginByCoep —
credentialless only exempts the final non-redirected response, not a
cross-origin redirect hop. placehold.co returns its image directly with no
redirect, which avoids that failure mode entirely.
"""
import logging
import re
import requests
from typing import Any, Dict, Optional
from urllib.parse import quote

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

PIXABAY_SEARCH_URL = "https://pixabay.com/api/"
REQUEST_TIMEOUT_SECONDS = 4
CACHE_KEY_PREFIX = "img:pixabay:"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "image"


def _placeholder_url(query: str, width: int = 800, height: int = 600) -> str:
    return f"https://placehold.co/{width}x{height}?text={quote(query)}"


def _search_pixabay(query: str) -> Optional[str]:
    api_key = getattr(settings, "PIXABAY_API_KEY", None)
    if not api_key:
        return None

    try:
        response = requests.get(
            PIXABAY_SEARCH_URL,
            params={"key": api_key, "q": query, "image_type": "photo", "per_page": 3},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.warning(f"Pixabay search failed ({response.status_code}) for query={query!r}")
            return None

        hits = response.json().get("hits", [])
        if not hits:
            return None

        return hits[0].get("largeImageURL") or hits[0].get("webformatURL")
    except Exception as e:
        logger.warning(f"Pixabay search errored for query={query!r}: {e}")
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

    url = _search_pixabay(query)
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
    max_calls = getattr(settings, "IMAGE_SEARCH_MAX_CALLS_PER_GENERATION", 10)
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
