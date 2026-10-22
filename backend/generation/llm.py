import hashlib
import json
import logging
import os
import random
import re
import secrets
import time
import requests
from typing import Optional, Dict, Any
from django.conf import settings

from .llm_models import DEFAULT_UI_MODEL, make_model_id, parse_model_id, reasoning_model_for

logger = logging.getLogger(__name__)


from .errors import (  # noqa: E402  (typed, user-safe errors; see errors.py)
    LLMError,
    LLMInvalidResponseError,
    LLMRateLimitError,
    LLMUnavailableError,
    error_from_response,
    gemini_text,
    groq_text,
    provider_call,
)

def _json_body(provider: str, response) -> Dict[str, Any]:
    """A 200 response's JSON object, or LLMInvalidResponseError."""
    try:
        data = response.json()
    except ValueError:
        logger.error(f"{provider} returned a non-JSON 200 response")
        raise LLMInvalidResponseError() from None
    if not isinstance(data, dict):
        raise LLMInvalidResponseError()
    return data


# Old names, kept importable.
ModelUnavailableError = LLMUnavailableError
RateLimitError = LLMRateLimitError

GROQ_API_KEY = settings.GROQ_AI_API_KEY
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

GEMINI_API_KEY = settings.GEMINI_API_KEY
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# ===========================================================================
# COLOUR THEMING
#
# Named palettes, chosen by the project's subject and mood. Each has a light
# and a dark variant; both carry a saturated primary and a bold accent. The
# planner gets a per-request palette hint (seeded from the prompt + a random
# salt) so identical prompts don't converge on one look, and may override it.
# Hex values are Tailwind palette colours; `families` are the Tailwind colour
# families for secondary elements (all are safelisted in the frontend's
# edit-mode build).
# ===========================================================================

PALETTES: Dict[str, Dict[str, Any]] = {
    "ocean": {
        "description": "deep sea blues with a coral accent; calm, trustworthy, fresh",
        "families": ("sky", "blue", "cyan"),
        "light": {"background": "#bae6fd", "surface": "#f0f9ff", "primary": "#0369a1", "secondary": "#1d4ed8", "accent": "#f97316", "hero": ("#0369a1", "#1d4ed8")},
        "dark": {"background": "#082f49", "surface": "#0c4a6e", "primary": "#38bdf8", "secondary": "#22d3ee", "accent": "#fb923c", "hero": ("#0c4a6e", "#1e3a8a")},
    },
    "sunset": {
        "description": "warm orange-to-rose glow with a violet accent; welcoming, energetic",
        "families": ("orange", "rose", "amber"),
        "light": {"background": "#fed7aa", "surface": "#fff7ed", "primary": "#c2410c", "secondary": "#be123c", "accent": "#7c3aed", "hero": ("#c2410c", "#be123c")},
        "dark": {"background": "#431407", "surface": "#7c2d12", "primary": "#fb923c", "secondary": "#fb7185", "accent": "#fbbf24", "hero": ("#7c2d12", "#881337")},
    },
    "forest": {
        "description": "lush greens with an amber accent; natural, healthy, sustainable",
        "families": ("emerald", "green", "lime"),
        "light": {"background": "#bbf7d0", "surface": "#f0fdf4", "primary": "#047857", "secondary": "#15803d", "accent": "#d97706", "hero": ("#047857", "#15803d")},
        "dark": {"background": "#022c22", "surface": "#064e3b", "primary": "#34d399", "secondary": "#a3e635", "accent": "#fbbf24", "hero": ("#064e3b", "#14532d")},
    },
    "candy": {
        "description": "bubblegum pinks and purples with a cyan pop; playful, sweet, youthful",
        "families": ("pink", "fuchsia", "purple"),
        "light": {"background": "#fbcfe8", "surface": "#fdf2f8", "primary": "#be185d", "secondary": "#9333ea", "accent": "#0891b2", "hero": ("#be185d", "#9333ea")},
        "dark": {"background": "#500724", "surface": "#831843", "primary": "#f472b6", "secondary": "#c084fc", "accent": "#22d3ee", "hero": ("#831843", "#581c87")},
    },
    "neon": {
        "description": "electric cyan and magenta with a lime spark; bold, techy, nightlife, gaming",
        "families": ("cyan", "fuchsia", "lime"),
        "light": {"background": "#a5f3fc", "surface": "#ecfeff", "primary": "#a21caf", "secondary": "#0e7490", "accent": "#65a30d", "hero": ("#a21caf", "#0e7490")},
        "dark": {"background": "#1e1b4b", "surface": "#312e81", "primary": "#22d3ee", "secondary": "#e879f9", "accent": "#a3e635", "hero": ("#312e81", "#701a75")},
    },
    "earth": {
        "description": "terracotta, clay and honey with a teal accent; grounded, artisanal, organic",
        "families": ("amber", "orange", "yellow"),
        "light": {"background": "#fde68a", "surface": "#fffbeb", "primary": "#b45309", "secondary": "#9a3412", "accent": "#0d9488", "hero": ("#b45309", "#9a3412")},
        "dark": {"background": "#451a03", "surface": "#78350f", "primary": "#fbbf24", "secondary": "#fb923c", "accent": "#2dd4bf", "hero": ("#78350f", "#7c2d12")},
    },
    "berry": {
        "description": "rich violets and raspberry with a gold accent; creative, luxurious, expressive",
        "families": ("violet", "purple", "rose"),
        "light": {"background": "#ddd6fe", "surface": "#f5f3ff", "primary": "#6d28d9", "secondary": "#be185d", "accent": "#d97706", "hero": ("#6d28d9", "#be185d")},
        "dark": {"background": "#2e1065", "surface": "#4c1d95", "primary": "#a78bfa", "secondary": "#f472b6", "accent": "#fbbf24", "hero": ("#4c1d95", "#831843")},
    },
    "midnight": {
        "description": "indigo and royal blue with an amber accent; confident, premium, corporate",
        "families": ("indigo", "blue", "slate"),
        "light": {"background": "#c7d2fe", "surface": "#eef2ff", "primary": "#4338ca", "secondary": "#1d4ed8", "accent": "#d97706", "hero": ("#4338ca", "#1d4ed8")},
        "dark": {"background": "#0f172a", "surface": "#1e293b", "primary": "#818cf8", "secondary": "#60a5fa", "accent": "#fbbf24", "hero": ("#1e1b4b", "#1e3a8a")},
    },
    "citrus": {
        "description": "zesty lime and lemon with an orange-pink kick; fresh, sporty, upbeat",
        "families": ("lime", "yellow", "orange"),
        "light": {"background": "#fef08a", "surface": "#fefce8", "primary": "#4d7c0f", "secondary": "#c2410c", "accent": "#db2777", "hero": ("#4d7c0f", "#c2410c")},
        "dark": {"background": "#1a2e05", "surface": "#365314", "primary": "#a3e635", "secondary": "#facc15", "accent": "#fb923c", "hero": ("#365314", "#713f12")},
    },
    "monochrome": {
        "description": "crisp zinc greys with one bold red accent; editorial, minimal, high-contrast",
        "families": ("zinc", "slate", "red"),
        "light": {"background": "#e4e4e7", "surface": "#fafafa", "primary": "#18181b", "secondary": "#3f3f46", "accent": "#dc2626", "hero": ("#18181b", "#3f3f46")},
        "dark": {"background": "#09090b", "surface": "#27272a", "primary": "#fafafa", "secondary": "#a1a1aa", "accent": "#ef4444", "hero": ("#18181b", "#450a0a")},
    },
}

# Subject keywords -> palettes that suit them. The hint picks among these (or
# among all palettes when nothing matches). Order doesn't encode preference.
SUBJECT_PALETTES = [
    (("pet", "dog", "cat", "puppy", "vet", "animal"), ("candy", "earth", "citrus", "sunset")),
    (("kid", "child", "school", "toy", "nursery", "learning", "education"), ("candy", "citrus", "sunset", "ocean")),
    (("law", "legal", "attorney", "consult", "insurance", "accounting", "corporate", "agency", "b2b"), ("midnight", "ocean", "monochrome", "berry", "earth")),
    (("fintech", "finance", "bank", "crypto", "trading", "invest", "payment", "saas", "dashboard", "analytics"), ("midnight", "ocean", "forest", "neon", "berry")),
    (("yoga", "wellness", "spa", "meditation", "health", "fitness", "therapy", "mindful"), ("forest", "earth", "ocean", "berry")),
    (("game", "gaming", "esport", "music", "festival", "club", "nightlife", "concert"), ("neon", "berry", "candy", "midnight")),
    (("restaurant", "cafe", "coffee", "food", "bakery", "pizza", "bistro", "recipe", "kitchen"), ("sunset", "earth", "citrus", "berry")),
    (("portfolio", "designer", "photograph", "artist", "creative", "blog", "magazine", "fashion"), ("monochrome", "berry", "sunset", "neon", "ocean")),
    (("travel", "hotel", "beach", "surf", "tour", "airline", "resort"), ("ocean", "sunset", "citrus", "forest")),
    (("eco", "garden", "farm", "plant", "organic", "solar", "climate", "outdoor", "hiking"), ("forest", "earth", "citrus")),
    (("tech", "startup", "ai", "developer", "software", "app", "cloud", "cyber"), ("neon", "midnight", "ocean", "berry", "citrus")),
    (("luxury", "jewel", "wine", "boutique", "wedding", "beauty", "cosmetic", "salon"), ("berry", "monochrome", "earth", "candy")),
    (("sport", "gym", "running", "football", "soccer", "team", "athlet"), ("citrus", "sunset", "neon", "ocean")),
]

# Only an explicit request flips the mode; "modern/professional/sleek" don't.
DARK_WORDS = ("dark mode", "dark theme", "dark ", "night", "black background", "noir", "cyberpunk", "neon")
LIGHT_WORDS = ("light mode", "light theme", "bright", "airy", "white background")
DEFAULT_DARK_PROBABILITY = 0.3
DARK_LEANING_PALETTES = {"neon": 0.6, "midnight": 0.45}

_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
LIGHT_TEXT = "#f8fafc"
DARK_TEXT = "#0f172a"
LIGHT_MUTED = "#cbd5e1"
DARK_MUTED = "#334155"


def _is_hex(value: Any) -> bool:
    return isinstance(value, str) and bool(_HEX_RE.match(value))


def _rgb(hex_color: str):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def relative_luminance(hex_color: str) -> float:
    def channel(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in _rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float:
    la, lb = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def readable_text_on(background: str) -> str:
    """Near-black or near-white, whichever contrasts more with `background`."""
    return LIGHT_TEXT if contrast_ratio(LIGHT_TEXT, background) >= contrast_ratio(DARK_TEXT, background) else DARK_TEXT


def _mentions(text: str, keyword: str) -> bool:
    """Keyword at a word start ("pet" matches "pets", not "carpet"); short
    keywords must be whole words ("ai" doesn't match "mail")."""
    pattern = rf"\b{re.escape(keyword)}s?\b" if len(keyword) <= 3 else rf"\b{re.escape(keyword)}"
    return re.search(pattern, text) is not None


def choose_palette_hint(prompt: str, salt: Optional[str] = None) -> Dict[str, str]:
    """Pick a palette + mode suggestion for this request.

    Seeded from the prompt plus a random salt: the same prompt gets different
    (but subject-appropriate) palettes across requests, while a fixed salt
    makes the choice reproducible for tests and evaluation.
    """
    text = f" {(prompt or '').lower()} "
    salt = secrets.token_hex(8) if salt is None else salt
    rng = random.Random(hashlib.sha256(f"{salt}\0{text}".encode()).hexdigest())

    # Palettes from the best-matching subject group(s): "pet store for dog
    # toys" is about pets (2 hits), not kids ("toy", 1 hit).
    scores = [(sum(_mentions(text, k) for k in keywords), palettes) for keywords, palettes in SUBJECT_PALETTES]
    best = max(score for score, _ in scores)
    candidates: list = []
    for score, palettes in scores:
        if best and score == best:
            candidates.extend(p for p in palettes if p not in candidates)
    reason = "subject match" if candidates else "no subject match; random palette"
    palette = rng.choice(candidates or sorted(PALETTES))

    if any(w in text for w in DARK_WORDS):
        mode = "dark"
    elif any(w in text for w in LIGHT_WORDS):
        mode = "light"
    else:
        mode = "dark" if rng.random() < DARK_LEANING_PALETTES.get(palette, DEFAULT_DARK_PROBABILITY) else "light"
    return {"palette": palette, "mode": mode, "reason": reason}


def build_color_scheme(palette: str, mode: str) -> Dict[str, Any]:
    """The full theme.color_scheme for a named palette variant.

    Keeps the original contract (mode/background/surface/primary/accent) and
    adds optional keys: palette, secondary, text, muted_text, on_primary, hero.
    """
    variant = PALETTES[palette]["dark" if mode == "dark" else "light"]
    return _complete_scheme({**variant, "palette": palette, "mode": "dark" if mode == "dark" else "light"})


def _complete_scheme(scheme: Dict[str, Any]) -> Dict[str, Any]:
    """Derive text colours and hero stops so every scheme is readable."""
    scheme = dict(scheme)
    background = scheme["background"]
    if not _is_hex(scheme.get("text")) or contrast_ratio(scheme["text"], background) < 4.5:
        scheme["text"] = readable_text_on(background)
    scheme["muted_text"] = DARK_MUTED if scheme["text"] == DARK_TEXT else LIGHT_MUTED
    scheme["on_primary"] = readable_text_on(scheme["primary"])
    hero = scheme.get("hero")
    if not (isinstance(hero, (list, tuple)) and len(hero) == 2 and all(_is_hex(h) for h in hero)):
        hero = (scheme["primary"], scheme["secondary"]) if scheme["mode"] == "light" else (scheme["surface"], scheme["background"])
    scheme["hero"] = list(hero)
    # Text over the whole gradient: whichever colour's worst stop is best.
    scheme["on_hero"] = max((LIGHT_TEXT, DARK_TEXT), key=lambda c: min(contrast_ratio(c, h) for h in hero))
    return scheme


def normalize_color_scheme(design_plan: Dict[str, Any], hint: Dict[str, str]) -> Dict[str, Any]:
    """Make theme.color_scheme complete and valid, in place.

    The planner's own valid hex values always win (it may have honoured
    user-specified colours). Missing/invalid keys are filled from the palette
    it named, else from the hint. Text colours are re-derived for contrast.
    """
    theme = design_plan.get("theme")
    if not isinstance(theme, dict):
        theme = design_plan["theme"] = {}
    planned = theme.get("color_scheme")
    planned = planned if isinstance(planned, dict) else {}

    palette = planned.get("palette") if planned.get("palette") in PALETTES else None
    mode = planned.get("mode")
    if mode not in ("light", "dark"):
        # Old modes ("vibrant", "soft") or none: infer from the background.
        bg = planned.get("background")
        mode = ("dark" if relative_luminance(bg) < 0.2 else "light") if _is_hex(bg) else hint["mode"]

    base = build_color_scheme(palette or hint["palette"], mode)
    scheme = {**base}
    for key in ("background", "surface", "primary", "secondary", "accent", "text"):
        if _is_hex(planned.get(key)):
            scheme[key] = planned[key]
    # Canonical hero stops only while the colours are the palette's own;
    # otherwise re-derive them from the (custom) colours.
    if planned.get("hero") is not None:
        scheme["hero"] = planned["hero"]
    elif any(scheme[k] != base[k] for k in ("primary", "secondary", "surface", "background")):
        scheme.pop("hero", None)
    scheme["palette"] = palette or (planned.get("palette") if isinstance(planned.get("palette"), str) else None) or hint["palette"]
    scheme["mode"] = mode
    theme["color_scheme"] = _complete_scheme(scheme)
    return theme["color_scheme"]


def palette_catalog_text() -> str:
    lines = []
    for name, p in PALETTES.items():
        light, dark = p["light"], p["dark"]
        lines.append(
            f'   - {name}: {p["description"]}. Tailwind families: {", ".join(p["families"])}.\n'
            f'       light: background {light["background"]}, surface {light["surface"]}, primary {light["primary"]}, secondary {light["secondary"]}, accent {light["accent"]}\n'
            f'       dark:  background {dark["background"]}, surface {dark["surface"]}, primary {dark["primary"]}, secondary {dark["secondary"]}, accent {dark["accent"]}'
        )
    return "\n".join(lines)


def palette_hint_text(hint: Dict[str, str]) -> str:
    return (
        "\n\n---\n"
        f"PALETTE HINT (for variety): palette \"{hint['palette']}\", mode \"{hint['mode']}\".\n"
        "Use it unless the subject or the user's request clearly fits another palette or mode better, "
        "or the user specified colours (then honour them and set palette to \"custom\")."
    )


def colour_guidance(scheme: Dict[str, Any]) -> str:
    """Stage-2 colour system: exact arbitrary-value classes from the planner's
    hex colours, plus Tailwind families for secondary elements, with a tiny
    worked example in this palette."""
    s = scheme
    dark = s["mode"] == "dark"
    families = PALETTES.get(s.get("palette"), {}).get("families") or ("indigo", "purple", "pink")
    fam = families[0]
    tint = f"bg-{fam}-900 text-{fam}-200 border-{fam}-700" if dark else f"bg-{fam}-100 text-{fam}-800 border-{fam}-300"
    icon = f"text-{fam}-400" if dark else f"text-{fam}-600"
    hero_from, hero_to = s["hero"]
    example = json.dumps({
        "type": "Hero",
        "props": {"className": f"bg-gradient-to-br from-[{hero_from}] to-[{hero_to}] text-[{s['on_hero']}] rounded-2xl p-12"},
        "children": [
            {"type": "Text", "props": {"tag": "h1", "className": f"text-5xl font-bold text-[{s['on_hero']}]"}, "content": "…"},
            {"type": "Button", "props": {"className": f"bg-[{s['accent']}] text-[{readable_text_on(s['accent'])}] font-semibold px-6 py-3 rounded-xl hover:opacity-90"}, "content": "…"},
        ],
    })
    card = json.dumps({
        "type": "Card",
        "props": {"className": f"bg-[{s['surface']}] text-[{readable_text_on(s['surface'])}] rounded-xl p-6 shadow-md border border-{fam}-{'700' if dark else '200'}"},
        "children": [
            {"type": "Icon", "props": {"name": "Star", "className": f"w-8 h-8 {icon}"}},
            {"type": "Text", "props": {"className": f"text-xs font-semibold px-2 py-1 rounded-full {tint}"}, "content": "…"},
        ],
    })
    return f"""COLOUR SYSTEM (palette: {s.get('palette')}, mode: {s['mode']}) — use these exact classes:
- Page background (Root): bg-[{s['background']}] with body text text-[{s['text']}], muted text text-[{s['muted_text']}]
- Hero: bg-gradient-to-br from-[{hero_from}] to-[{hero_to}] with text-[{s['on_hero']}]
- Primary buttons / CTAs: bg-[{s['primary']}] text-[{s['on_primary']}] hover:opacity-90
- Bold accent (at least once per page: badges, highlights, key numbers, secondary CTA): bg-[{s['accent']}] / text-[{s['accent']}]
- Secondary gradient (feature band, banners): from-[{s['primary']}] to-[{s['secondary']}]
- Card surfaces: bg-[{s['surface']}] (white only for small cards on a coloured section)
- Secondary elements (chips, icon tiles, borders, table stripes): Tailwind families {', '.join(families)}, e.g. {tint}; icons {icon}
- Section rhythm: alternate page background bg-[{s['background']}], surface bg-[{s['surface']}], and a saturated band bg-[{s['primary']}] text-[{s['on_primary']}]; adjacent sections never share a background
- Worked example (hero): {example}
- Worked example (card): {card}"""


_COLOR_TOKEN_RE = re.compile(r"\{\{\s*(background|surface|primary|secondary|accent|text|muted_text|on_primary|on_hero|hero_from|hero_to)\s*\}\}")


def resolve_color_tokens(node: Any, scheme: Dict[str, Any]) -> Any:
    """Replace {{primary}}-style tokens (from the system prompt's generic
    examples) left in className strings with the scheme's hex values."""
    values = {**scheme, "hero_from": scheme["hero"][0], "hero_to": scheme["hero"][1]}
    if isinstance(node, dict):
        props = node.get("props")
        if isinstance(props, dict) and isinstance(props.get("className"), str):
            props["className"] = _COLOR_TOKEN_RE.sub(lambda m: str(values[m.group(1)]), props["className"])
        for child in node.get("children") or []:
            resolve_color_tokens(child, scheme)
    return node


# Colour utilities in free-form planner text (typography scale...) would
# contradict the COLOUR SYSTEM and, on a dark page, make text unreadable.
_COLOUR_UTILITY_RE = re.compile(
    r"(?<!\S)(?:[a-z-]+:)*-?(?:text|bg|border|from|via|to|ring|fill|stroke|shadow|decoration|accent|caret|divide|outline)-"
    r"(?:white|black|transparent|current|[a-z]+-\d{2,3}(?:/\d+)?|\[(?:#|rgb|hsl|oklch|color:)[^\]]*\](?:/\d+)?)(?!\S)"
)


def strip_colour_classes(text: Any) -> str:
    """`text-4xl font-bold text-gray-900` -> `text-4xl font-bold`. Only used on
    prompt text; never touches a schema."""
    if not isinstance(text, str):
        return ""
    return " ".join(_COLOUR_UTILITY_RE.sub(" ", text).split())


def _temperature(setting: str, default: float) -> float:
    """settings.<SETTING> or the env var of the same name, clamped to 0-1.5."""
    raw = getattr(settings, setting, None)
    if raw is None:
        raw = os.environ.get(setting)
    try:
        value = float(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default
    return min(max(value, 0.0), 1.5)


PLANNER_SYSTEM_PROMPT = """
You are a reasoning-first UI architect.

Your responsibilities:
1. Infer intent and page category
2. Decide layout archetype
3. Decide required and forbidden UI patterns
4. Generate a design_plan JSON
5. Give a project name in 5 to 200 characters in key name project_name as string
6. Give a project description in 10 to 500 characters in key name project_description as string
7. If the page represents a product that need to showcase image:
   - Generate a list of products
   - Each product MUST include:
     { name, price }
   - Decorative images are forbidden
   
8. COLOR THEME — pick ONE named palette and a mode:
   Choose the palette from the project's SUBJECT and mood (what it is about,
   who it is for), not from generic style words. "modern", "professional",
   "sleek", "clean" or "elegant" do NOT imply dark mode. Use dark only when the
   user asks for it or the subject is genuinely night-time (gaming, nightlife,
   cinema). Every variant has a saturated primary and a bold accent; light
   variants have a clearly coloured page background, never white.

   PALETTES:
__PALETTE_CATALOG__

   The user message ends with a PALETTE HINT chosen for variety. Follow it
   unless the subject clearly suits another palette or mode better. If the user
   specifies colours (e.g. a <color_scheme> block or named colours), honour
   them, derive the remaining colours to match, and set palette to "custom".

   Output this in theme.color_scheme (copy the chosen variant's hex values):
   {
     "palette": "<palette name or custom>",
     "mode": "light" | "dark",
     "background": "#hex",
     "surface": "#hex",
     "primary": "#hex",
     "secondary": "#hex",
     "accent": "#hex"
   }

You must DISCOVER the layout — not assume it.

The key "design_plan.sections" MUST always be a list of objects:
{ name: string, type: string, content: string }

Do NOT include login/signup unless explicitly requested.

RETURN ONLY VALID JSON.
""".replace("__PALETTE_CATALOG__", palette_catalog_text())


UI_GENERATOR_SYSTEM_PROMPT = """You are an expert React/Tailwind developer specializing in modern, polished UI design.
Your job is to convert a `design_plan` into a VALID JSON UI SCHEMA with RICH, REALISTIC CONTENT.

-------------------------------------------
STRICT OUTPUT FORMAT
-------------------------------------------
{
  "title": "Page Title",
  "schema": { ...Root Component... },
  "code": "",
  "metadata": { "framework": "react", "tailwindVersion": "4" }
}

-------------------------------------------
COMPONENT SCHEMA RULES
-------------------------------------------
1. Structure: {"type": "Component", "props": {...}, "children": []}
2. Text Content: Use "content": "Text" (Do not use children for raw text).
3. NO Raw HTML: Never put <tags> inside a string. Use "type": "Link" or "Text".
4. NO PLACEHOLDERS: Generate actual, realistic content based on the design plan.
5. Text must contrast with what it sits on: dark text on light surfaces, light text (white is fine)
   on dark or saturated backgrounds.
6. NEVER invent an image URL. For every Image component, leave "src" as an empty string ("") and
   instead write a concrete, specific "alt" text (3-8 words naming the actual subject, e.g.
   "golden retriever puppy on green grass" — not "product image" or "placeholder"). The backend
   resolves a real photo from that "alt" text after generation.

Allowed Types:
Root, Section, Container, Card, CardHeader, CardTitle, CardContent,
Form, Label, Input, Button, Text, Link, Icon, Image, Div,
Hero, Timeline, TimelineItem, Grid, Flex

-------------------------------------------
COLOURS
-------------------------------------------
The user message contains a COLOUR SYSTEM with exact hex values for this page. Build colours from it
with Tailwind arbitrary values (Tailwind v4): bg-[#0f172a], text-[#fbbf24], border-[#334155],
bg-gradient-to-br from-[#667eea] to-[#ec4899]. In the examples below, {{background}}, {{surface}},
{{primary}}, {{secondary}}, {{accent}}, {{text}}, {{muted_text}}, {{on_primary}}, {{on_hero}},
{{hero_from}} and {{hero_to}} stand for those hex values: write the hex value (e.g. bg-[#0369a1]).
Rules:
- Root gets the COLOUR SYSTEM page background. Never bg-white, from-white, via-white or from-gray-50
  on Root, Hero or Section backgrounds.
- The Hero is a saturated gradient (hero_from -> hero_to), never a pale or white one.
- Every page uses the bold accent at least once.
- Adjacent sections never share the same background: alternate page background, surface, and a
  saturated primary band.
- Light themes use saturated 400-700 shades for colour and tinted (not white) section backgrounds;
  white is only for small card surfaces.
- Keep text readable: dark text on light surfaces, light text on dark or saturated ones.
- The preview is plain Tailwind v4 with no theme: shadcn colour tokens (bg-primary, bg-background, bg-card,
  bg-muted, text-foreground, text-muted-foreground, border-border...) do not exist there and render with NO
  colour. Always use palette colours (bg-rose-600) or the exact hex values (bg-[#0369a1]).
- Opacity goes in the colour (bg-blue-500/50, text-white/80, bg-[#0f172a]/90); v3 helpers such as
  bg-opacity-50 or text-opacity-80 no longer exist and do nothing.
- Root also gets min-h-screen so its background fills the page.

-------------------------------------------
CRITICAL: GENERATE REAL CONTENT, NOT PLACEHOLDERS
-------------------------------------------
NEVER use placeholder text like "Stats Counter" or "Trophy Gallery".
ALWAYS generate:
- Actual numbers, metrics, and data points
- Realistic titles, descriptions, and labels
- Meaningful content that matches the design plan's intent
- Proper icons that match the content context

-------------------------------------------
MODERN UI PATTERNS (IMPLEMENT THESE)
-------------------------------------------

1. STATS COUNTERS:
   Structure each stat as a Card with:
   - An Icon at the top (use appropriate icon: Users, TrendingUp, Star, Award, Target, etc.)
   - A large, bold number (use text-3xl or text-4xl font-bold)
   - A descriptive label below (text-sm in the COLOUR SYSTEM muted text colour)
   - Modern styling: rounded-xl, shadow-md, the COLOUR SYSTEM card surface
   - Icon in the accent or a palette family colour
   
   Example structure:
   {
     "type": "Card",
     "props": {"className": "p-6 rounded-xl shadow-md bg-[{{surface}}]"},
     "children": [
       {"type": "Icon", "props": {"name": "Users", "className": "w-8 h-8 text-[{{accent}}] mb-3"}},
       {"type": "Text", "props": {"className": "text-4xl font-bold text-[{{text}}] mb-1"}, "content": "12k+"},
       {"type": "Text", "props": {"className": "text-sm text-[{{muted_text}}]"}, "content": "Active Users"}
     ]
   }

2. TROPHY/AWARD GALLERIES:
   Create a responsive grid of trophy cards with:
   - Card with rounded corners and shadow
   - Trophy icon or image placeholder
   - Title text (trophy name)
   - Optional subtitle (date or achievement)
   - Hover effects suggested via className
   
   Example:
   {
     "type": "Card",
     "props": {"className": "p-6 rounded-xl shadow-md bg-[{{surface}}] border-l-4 border-[{{accent}}] hover:shadow-lg transition-shadow"},
     "children": [
       {"type": "Icon", "props": {"name": "Trophy", "className": "w-12 h-12 text-[{{accent}}] mb-3"}},
       {"type": "Text", "props": {"className": "text-lg font-semibold text-[{{text}}]"}, "content": "World Cup 2022"},
       {"type": "Text", "props": {"className": "text-sm text-[{{muted_text}}] mt-1"}, "content": "FIFA World Cup Champion"}
     ]
   }

3. HERO SECTIONS:
   Use type "Hero" for hero sections:
   - Large, prominent heading (text-5xl or text-6xl font-bold)
   - Descriptive subtitle (text-xl, same text colour as the heading at opacity-90)
   - Background: the COLOUR SYSTEM hero gradient (saturated, never pale or white)
   - Centered or left-aligned layout
   - Generous padding (p-12 or p-16)
   - Rounded corners: rounded-2xl
   - Shadow: shadow-lg
   
   Example:
   {
     "type": "Hero",
     "props": {"className": "bg-gradient-to-br from-[{{hero_from}}] to-[{{hero_to}}] rounded-2xl shadow-lg p-12 text-center"},
     "children": [
       {"type": "Text", "props": {"className": "text-5xl font-bold text-[{{on_hero}}] mb-4"}, "content": "Lionel Messi: The Record Breaker"},
       {"type": "Text", "props": {"className": "text-xl text-[{{on_hero}}] opacity-90"}, "content": "A legendary career marked by unparalleled achievements"},
       {"type": "Button", "props": {"className": "mt-8 bg-[{{accent}}] font-semibold px-6 py-3 rounded-xl hover:opacity-90"}, "content": "Explore the records"}
     ]
   }

4. TIMELINES:
   Use type "Timeline" for timeline containers and "TimelineItem" for each entry:
   - Timeline container: Use "Timeline" type with relative positioning and left border
   - Each timeline item: Use "TimelineItem" type
   - Year/date prominently displayed (text-2xl font-bold)
   - Achievement description (text-sm, muted text colour)
   - Each item is a tinted surface (the COLOUR SYSTEM surface colour) with an accent left border
   
   Example:
   {
     "type": "Timeline",
     "props": {"className": "relative pl-8 border-l-2 border-[{{primary}}] space-y-8"},
     "children": [
       {
         "type": "TimelineItem",
         "props": {"className": "relative bg-[{{surface}}] rounded-lg p-6 shadow-md border-l-4 border-[{{accent}}]"},
         "children": [
           {"type": "Text", "props": {"className": "text-2xl font-bold text-[{{primary}}] mb-1"}, "content": "2004"},
           {"type": "Text", "props": {"className": "text-sm text-[{{muted_text}}]"}, "content": "Debut for Barcelona"}
         ]
       }
     ]
   }

5. TESTIMONIAL CAROUSELS:
   - Card-based testimonials
   - Quote text in italic
   - Author name and role
   - Optional avatar icon

6. ICONS (lucide-react):
   Use appropriate icons from lucide-react. Common icons:
   - Users, User, UserCheck (for user-related stats)
   - TrendingUp, TrendingDown, BarChart (for metrics)
   - Star, Award, Trophy (for achievements)
   - Target, Goal, Zap (for performance)
   - Calendar, Clock (for time-related)
   - Mail, Phone, MessageSquare (for contact)
   - Github, Twitter, Linkedin (for social)
   - LayoutDashboard, Settings, Home (for navigation)
   - ArrowRight, ArrowLeft, ChevronRight (for navigation)
   - Check, X, AlertCircle (for status)
   
   Format: {"type": "Icon", "props": {"name": "IconName", "className": "w-6 h-6 text-[{{accent}}]"}}

7. MODERN STYLING GUIDELINES:
   - Use rounded-xl or rounded-2xl for modern card corners
   - Apply shadow-md or shadow-lg for depth
   - Colours: follow the COLOUR SYSTEM in the user message (see COLOURS above); secondary elements
     use the palette's Tailwind families listed there
   - Spacing: Use p-6 or p-8 for card padding, gap-6 for grid spacing
   - Typography: Use font-bold for headings, font-semibold for subheadings
   - Text sizes: text-4xl or text-5xl for hero numbers, text-2xl for section titles

   - SECTION STRUCTURE: Always wrap sections with proper padding (py-12 px-4 sm:px-6 lg:px-8)
   - CONTAINERS: Use max-w-7xl mx-auto for main containers to prevent content from stretching too wide

8. CARDS:
   Follow the Shadcn pattern:
   Card -> CardHeader (optional) -> CardContent -> CardFooter (optional).
   
   Card background: the COLOUR SYSTEM card surface bg-[{{surface}}] with text-[{{text}}].
   On a saturated band, white cards are fine. Use 'shadow-md', 'rounded-xl', 'p-6', and a palette-family
   or accent border for emphasis.

9. LAYOUT:
   - Use responsive grids: grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6
   - Full-width sections: w-full py-16 or py-20
   - Container max-width: max-w-7xl mx-auto px-4
   - Centered content: flex items-center justify-center

-------------------------------------------
CONTENT GENERATION RULES
-------------------------------------------
1. Read each section's "content" field carefully - it describes what should be displayed
2. Extract key information (numbers, achievements, dates) from the content description
3. Generate realistic data that matches the context (e.g., if it says "800+ goals", use "800+" not "Stats Counter")
4. Create meaningful labels and descriptions
5. Use appropriate icons that match the content theme
6. Apply the COLOUR SYSTEM from the user message

-------------------------------------------
EXECUTION
-------------------------------------------
Read the `design_plan` provided by the user carefully. 
For each section, generate REAL CONTENT based on the section's description.
Apply modern styling, appropriate icons, and realistic data.
Ensure the final JSON is valid and nest components correctly.
DO NOT use placeholder text - always generate actual, meaningful content.
"""


class LLMClient:
    """Two-stage LLM: Strategic Planning → Precision Building"""
    
    def __init__(self, ui_model_id: str = None):
        """
        Initialize client with model selection.

        Args:
            ui_model_id: Composite "provider:model" id (e.g.
                "groq:openai/gpt-oss-20b", "gemini:models/gemini-3.8-flash").
                Defaults to settings.DEFAULT_UI_MODEL. The planning/reasoning
                model is always the configured reasoning model for that same
                provider — never a different provider than the UI model.
        """
        self.ui_model_id = ui_model_id if ui_model_id else DEFAULT_UI_MODEL
        self.provider, self.ui_model = parse_model_id(self.ui_model_id)
        self.planning_model = reasoning_model_for(self.provider)

        self.timeout = 60
        # UI stage runs warmer for visual variety; planning stays steadier.
        # Override with LLM_UI_TEMPERATURE / LLM_PLANNER_TEMPERATURE (settings or env).
        self.ui_temperature = _temperature("LLM_UI_TEMPERATURE", 0.65)
        self.planner_temperature = _temperature("LLM_PLANNER_TEMPERATURE", 0.4)

        logger.info(f"LLMClient initialized: provider={self.provider}")
        logger.info(f"  Planning model: {self.planning_model}")
        logger.info(f"  UI generation model: {self.ui_model}")

    def generate_ui(self, user_prompt: str, retries: int = 3) -> Dict[str, Any]:
        """
        Two-stage generation:
        Stage 1: Strategic design planning with planning model
        Stage 2: UI generation with selected UI model
        """
        # STAGE 1: Planning with Moonshot (or other planning model)
        logger.info("🎨 STAGE 1: Creating strategic design plan...")
        palette_hint = choose_palette_hint(user_prompt)
        logger.info(f"  Palette hint: {palette_hint}")
        design_plan = self._call_planner(user_prompt + palette_hint_text(palette_hint), retries)
        # Fill/repair theme.color_scheme so stage 2 always has usable colours.
        normalize_color_scheme(design_plan, palette_hint)
        
        print(design_plan)
        print(":::::::::::::::::::::: NEXT :::::::::::::::::::")
        logger.info(f"✓ Design plan complete:")
        logger.info(f"  Project: {design_plan.get('project_name', 'Unknown')}")
        logger.info(f"  Style: {design_plan.get('theme', {}).get('style', 'Unknown')}")
        logger.info(f"  Primary color: {design_plan.get('theme', {}).get('color_scheme', {}).get('primary', 'Unknown')}")
        
        # STAGE 2: UI Generation with user-selected model
        logger.info("🔨 STAGE 2: Building UI from design plan...")
        ui_prompt = self._compile_ui_prompt(design_plan)
        ui_result = self._call_ui_generator(ui_prompt, design_plan, retries)
        if isinstance(ui_result.get("schema"), dict):
            resolve_color_tokens(ui_result["schema"], design_plan["theme"]["color_scheme"])
        
        print(ui_result)
        
        logger.info("✓ UI generation complete!")

        missing = [k for k in ("project_name", "project_description") if not isinstance(design_plan.get(k), str)]
        missing += [k for k in ("schema",) if not isinstance(ui_result.get(k), dict)]
        if missing:
            logger.error(f"LLM output missing required fields: {missing}")
            raise LLMInvalidResponseError()

        return {
            "project_name": design_plan["project_name"][:200],  # Enforce max 200
            "project_description": design_plan["project_description"][:500],  # Enforce max 500
            "design_plan": design_plan,
            "title": ui_result.get("title") or design_plan["project_name"][:200],
            "schema": ui_result["schema"],
            "metadata": ui_result.get("metadata") or {},
            "usage": {
                "planning_tokens": design_plan.get("usage", {}),
                "generation_tokens": ui_result.get("usage", {})
            },
            "models": {
                "provider": self.provider,
                "planning": make_model_id(self.provider, self.planning_model),
                "ui_generation": self.ui_model_id
            }
        }

    def _call_planner(self, prompt: str, retries: int) -> Dict[str, Any]:
        """Stage 1: Strategic design planning — same provider as the UI model."""
        for attempt in range(retries):
            try:
                if self.provider == "gemini":
                    return self._call_gemini(
                        prompt=prompt,
                        system_prompt=PLANNER_SYSTEM_PROMPT,
                        model=self.planning_model,
                        max_tokens=4096,
                        thinking_budget=-1,  # dynamic — planning quality benefits from thinking
                        temperature=self.planner_temperature,
                    )
                return self._call_groq_api(
                    prompt=prompt,
                    system_prompt=PLANNER_SYSTEM_PROMPT,
                    model=self.planning_model,
                    max_tokens=3500,
                    temperature=self.planner_temperature,
                )
            except LLMError as e:
                # Retry only what can succeed on a second try (overload,
                # timeout, malformed output); a rejected prompt, quota or
                # content block fails the same way every time.
                logger.warning(f"Planner attempt {attempt + 1}/{retries} failed: {e.error_code}")
                if e.retriable and attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
    
    def _call_ui_generator(self, prompt: str, design_plan: Dict, retries: int) -> Dict[str, Any]:
        """Stage 2: UI generation with user-selected model"""
        
        enhanced_prompt = self._build_ui_request(prompt, design_plan)

        for attempt in range(retries):
            try:
                if self.provider == "gemini":
                    return self._call_gemini(
                        prompt=enhanced_prompt,
                        system_prompt=UI_GENERATOR_SYSTEM_PROMPT,
                        model=self.ui_model,
                        max_tokens=16384,
                        thinking_budget=0,  # deterministic formatting — reserve the whole budget for output
                        temperature=self.ui_temperature,
                    )
                else:
                    return self._call_groq_api(
                        prompt=enhanced_prompt,
                        system_prompt=UI_GENERATOR_SYSTEM_PROMPT,
                        model=self.ui_model,
                        max_tokens=8192,
                        temperature=self.ui_temperature,
                    )
            except LLMError as e:
                # Retry only what can succeed on a second try (overload,
                # timeout, malformed output); a rejected prompt, quota or
                # content block fails the same way every time.
                logger.warning(f"UI Generator attempt {attempt + 1}/{retries} failed: {e.error_code}")
                if e.retriable and attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
    
    def _build_ui_request(self, prompt: str, design_plan: Dict[str, Any]) -> str:
        """Stage-2 user message: project context, the colour system built from
        the planner's hex colours, and the compiled section instructions."""
        theme = design_plan.get('theme') if isinstance(design_plan.get('theme'), dict) else {}
        typography = theme.get('typography', {}) if isinstance(theme.get('typography'), dict) else {}
        scheme = theme.get('color_scheme')
        if not (isinstance(scheme, dict) and {"hero", "on_hero", "muted_text", "on_primary"} <= scheme.keys()):
            # Not normalised yet (e.g. called directly): repair a copy.
            scheme = normalize_color_scheme(
                {"theme": {"color_scheme": dict(scheme) if isinstance(scheme, dict) else {}}},
                choose_palette_hint(design_plan.get('project_name', '')),
            )

        # Use .get() for design_system to prevent KeyError crash
        design_system = design_plan.get("design_system", {})
        spacing = design_system.get("spacing", "p-4 gap-4")
        radius = design_system.get("border_radius") or design_system.get("radius", "rounded-lg")

        return f"""PROJECT CONTEXT:
Project Name: {design_plan.get('project_name', '')}
Project Description: {design_plan.get('project_description', '')}

DESIGN SPECIFICATIONS:
THEME: {theme.get('style', 'modern')} (style words describe layout and typography, never colour: "minimal" or "clean" do not mean white or grey)
MODE: {scheme['mode']}
PALETTE: {scheme.get('palette')}
PRIMARY COLOR: {scheme['primary']}
SECONDARY COLOR: {scheme['secondary']}
BACKGROUND COLOR: {scheme['background']}
SURFACE COLOR: {scheme['surface']}
ACCENT COLOR: {scheme['accent']}
TYPOGRAPHY SCALE (sizes and weights only; colours come from the COLOUR SYSTEM): Hero: {strip_colour_classes(typography.get('heading')) or 'text-2xl font-bold'}, Body: {strip_colour_classes(typography.get('body')) or 'text-sm'}

SPACING SYSTEM: {spacing}
BORDER RADIUS: {radius}

{colour_guidance(scheme)}

BUILD INSTRUCTIONS:
{prompt}

CRITICAL REMINDERS:
1. Generate REAL CONTENT - extract actual numbers, achievements, and data from section descriptions
2. Use appropriate icons from lucide-react (see icon suggestions in sections above)
3. Apply modern styling: rounded-xl, shadow-md, gradients, proper spacing (p-6, gap-6)
4. DO NOT use placeholder text - always generate meaningful, realistic content
5. Use EXACT Tailwind classes; colours come from the COLOUR SYSTEM above as arbitrary values like bg-[{scheme['primary']}]
6. Build nested structures (Root → Section → Grid → Components)
7. Create polished, production-ready UI that matches modern design standards
8. The page must be clearly colourful: coloured page background, saturated hero, at least one bold accent,
   and no two adjacent sections with the same background. Never a white or near-white page."""

    def _call_groq_api(self, prompt: str, system_prompt: str, model: str, max_tokens: int = 4096, temperature: float = 0.4) -> Dict[str, Any]:
        """Call Groq API (supports multiple models via Groq)"""
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        logger.info(f"Calling Groq API with model: {model}")
        with provider_call("groq"):
            response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                raise error_from_response("groq", response)
            data = _json_body("groq", response)

        return self._parse_response(groq_text(data), data.get("usage", {}))
    
    def _call_gemini(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        max_tokens: int = 4096,
        thinking_budget: Optional[int] = None,
        temperature: float = 0.4,
    ) -> Dict[str, Any]:
        """Call Gemini API with the given model (e.g. "models/gemini-3.8-flash").

        thinking_budget: forwarded as generationConfig.thinkingConfig.thinkingBudget
            when given. Gemini 3.x models think by default, and thought tokens are
            drawn from the same maxOutputTokens budget as the visible response —
            left uncapped, a model can spend most of max_tokens thinking and
            truncate the actual output mid-JSON. Pass -1 for dynamic/unbounded
            thinking (planning stage, where reasoning quality matters) or 0 to
            disable thinking entirely (UI-generation stage, a deterministic
            formatting task where the full budget should go to visible output).
        """
        # Key in a header, not the URL: URLs end up in exception text and logs.
        headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY or ""}

        generation_config = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if thinking_budget is not None:
            generation_config["thinkingConfig"] = {"thinkingBudget": thinking_budget}

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": system_prompt},
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": generation_config
        }

        url = f"{GEMINI_BASE_URL}/{model}:generateContent"
        logger.info(f"Calling Gemini API with model: {model}")
        with provider_call("gemini"):
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                raise error_from_response("gemini", response)
            data = _json_body("gemini", response)

        return self._parse_response(gemini_text(data), data.get("usageMetadata", {}))
    
    def _parse_response(self, content: str, usage: Dict) -> Dict[str, Any]:
      """Extract and validate JSON from LLM response"""
      
      # Remove markdown code blocks
      if "```json" in content:
          content = content.split("```json")[1].split("```")[0]
      elif "```" in content:
          content = content.split("```")[1].split("```")[0]

      content = content.strip()
      
      import re
      
      # Remove other control characters that break JSON
      content = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', content)

      try:
          parsed = json.loads(content)
      except json.JSONDecodeError as e:
          logger.error(f"JSON Parse Error: {e}")
          logger.error(f"Content preview: {content[:500]}")
          
          if "Unterminated string" in str(e) or "Expecting value" in str(e):
              logger.warning("Attempting to fix truncated JSON...")
              
              try:
                  last_brace = content.rfind('}')
                  if last_brace > 0:
                      truncated = content[:last_brace + 1]
                      
                      open_braces = truncated.count('{')
                      close_braces = truncated.count('}')
                      while close_braces < open_braces:
                          truncated += '}'
                          close_braces += 1
                      
                      parsed = json.loads(truncated)
                      logger.info("Successfully recovered truncated JSON")
                  else:
                      raise LLMInvalidResponseError()
              except LLMInvalidResponseError:
                  raise
              except Exception as recovery_error:
                  logger.error(f"JSON recovery failed: {recovery_error}")
                  raise LLMInvalidResponseError() from None
          else:
              raise LLMInvalidResponseError() from None

      if not isinstance(parsed, dict):
          logger.error("LLM returned JSON that is not an object")
          raise LLMInvalidResponseError()
      parsed["usage"] = usage
      return parsed

    def _compile_ui_prompt(self, design_plan: Dict[str, Any]) -> str:
        archetype = design_plan.get("layout_archetype", "standard_layout")
        intent = design_plan.get("intent", "")
        required = design_plan.get("required_patterns", [])
        forbidden = design_plan.get("forbidden_patterns", [])

        design = design_plan.get("design_plan", {})
        sections = design.get("sections", [])

        lines = [
            f"PAGE INTENT: {intent}",
            f"LAYOUT ARCHETYPE: {archetype}",
            "",
            "REQUIRED UI PATTERNS:"
        ]

        for r in required:
            lines.append(f"- {r}")

        lines.append("")
        lines.append("FORBIDDEN UI PATTERNS:")
        for f in forbidden:
            lines.append(f"- {f}")

        lines.append("")
        lines.append("=" * 60)
        lines.append("DETAILED SECTIONS TO IMPLEMENT:")
        lines.append("=" * 60)
        lines.append("")
        
        # Icon mapping for different section types
        icon_suggestions = {
            "hero": ["Star", "Award", "Trophy", "Zap"],
            "stats": ["Users", "TrendingUp", "Star", "Award", "Target", "BarChart", "Zap", "Trophy"],
            "grid": ["Trophy", "Award", "Star", "Medal", "Crown"],
            "timeline": ["Calendar", "Clock", "History", "ArrowRight"],
            "carousel": ["Quote", "MessageSquare", "Users"],
            "footer": ["Github", "Twitter", "Linkedin", "Mail"]
        }
        
        for idx, section in enumerate(sections, 1):
            name = section.get("name", "unnamed")
            section_type = section.get("type", "")
            content_desc = section.get("content", "")
            
            lines.append(f"--- SECTION {idx}: {name} ({section_type}) ---")
            lines.append(f"Description: {content_desc}")
            
            # Provide implementation guidance based on section type
            if section_type == "hero":
                lines.append("Implementation: Create a full-width hero with large heading, subtitle, on the COLOUR SYSTEM hero gradient.")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("hero", ["Star"])))
            elif section_type == "stats":
                lines.append("Implementation: Create a grid of stat cards (typically 3-4 cards).")
                lines.append("Each card should have: Icon + Large Number + Label")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("stats", ["TrendingUp"])))
                lines.append("Extract actual numbers from the description (e.g., '800+ goals' -> display '800+')")
            elif section_type == "grid":
                lines.append("Implementation: Create a responsive grid (2-3 columns) of cards.")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("grid", ["Trophy"])))
                lines.append("Each card should represent a trophy/achievement with icon, title, and optional subtitle.")
            elif section_type == "timeline":
                lines.append("Implementation: Create a vertical or horizontal timeline with items.")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("timeline", ["Calendar"])))
                lines.append("Each item should show: Year/Date + Achievement Title + Description")
            elif section_type == "carousel":
                lines.append("Implementation: Create testimonial/quote cards in a grid or list.")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("carousel", ["Quote"])))
            elif section_type == "footer":
                lines.append("Implementation: Create a footer with links and social icons.")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("footer", ["Github"])))
            
            lines.append("")  # Empty line between sections

        lines.append("=" * 60)
        lines.append("")
        lines.append("CRITICAL INSTRUCTIONS:")
        lines.append("1. Generate REAL CONTENT - extract numbers, achievements, and data from section descriptions")
        lines.append("2. Use appropriate icons for each section type (see suggestions above)")
        lines.append("3. Apply modern styling: rounded-xl, shadow-md, gradients, proper spacing")
        lines.append("4. DO NOT use placeholder text like 'Stats Counter' or 'Trophy Gallery'")
        lines.append("5. Create meaningful titles, numbers, and labels based on the content descriptions")
        lines.append("6. Do NOT invent additional sections beyond those listed above")
        lines.append("7. Do NOT include authentication UI unless explicitly allowed")
        lines.append("8. Build a polished, production-ready UI that matches modern design standards")

        return "\n".join(lines)