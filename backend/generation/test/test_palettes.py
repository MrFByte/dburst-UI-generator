"""Colour theming: palette hints, color_scheme normalisation, stage-2 colour
guidance, token resolution, temperatures, and theme-aware codegen defaults."""
import copy
import re
from unittest.mock import patch

import pytest

from generation import llm
from generation.codegen import ReactCodeGenerator, render_schema
from generation.llm import (
    PALETTES,
    PLANNER_SYSTEM_PROMPT,
    UI_GENERATOR_SYSTEM_PROMPT,
    LLMClient,
    build_color_scheme,
    choose_palette_hint,
    colour_guidance,
    contrast_ratio,
    normalize_color_scheme,
    resolve_color_tokens,
)

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


# --------------------------------------------------------------------------
# (d) every named palette yields a valid, readable color_scheme
# --------------------------------------------------------------------------

@pytest.mark.parametrize("palette", sorted(PALETTES))
@pytest.mark.parametrize("mode", ["light", "dark"])
def test_every_palette_variant_is_valid_and_readable(palette, mode):
    s = build_color_scheme(palette, mode)
    # Original contract keys + the optional additions.
    for key in ("mode", "background", "surface", "primary", "accent"):
        assert key in s
    assert s["mode"] == mode and s["palette"] == palette
    for key in ("background", "surface", "primary", "secondary", "accent", "text", "muted_text", "on_primary", "on_hero"):
        assert HEX.match(s[key]), (key, s[key])
    assert len(s["hero"]) == 2 and all(HEX.match(h) for h in s["hero"])

    assert contrast_ratio(s["text"], s["background"]) >= 4.5
    assert contrast_ratio(s["text"], s["surface"]) >= 4.5
    assert contrast_ratio(s["muted_text"], s["background"]) >= 4.5
    assert contrast_ratio(s["on_primary"], s["primary"]) >= 4.5
    for stop in s["hero"]:
        assert contrast_ratio(s["on_hero"], stop) >= 4.5

    # Light pages are clearly coloured, never white; dark pages really are dark.
    if mode == "light":
        assert s["background"].lower() not in ("#ffffff", "#fff", "#fafafa")
        assert llm.relative_luminance(s["background"]) < 0.9
    else:
        assert llm.relative_luminance(s["background"]) < 0.05


def test_palette_families_are_frontend_safelisted_hues():
    safelisted = {"slate", "gray", "zinc", "red", "orange", "amber", "yellow", "lime", "green", "emerald",
                  "teal", "cyan", "sky", "blue", "indigo", "violet", "purple", "fuchsia", "pink", "rose"}
    for name, p in PALETTES.items():
        assert set(p["families"]) <= safelisted, name


def test_at_least_eight_palettes_with_distinct_primaries():
    assert len(PALETTES) >= 8
    primaries = {p["light"]["primary"] for p in PALETTES.values()}
    assert len(primaries) == len(PALETTES)


# --------------------------------------------------------------------------
# (a) palette hint: subject-driven, varied, and modern != dark
# --------------------------------------------------------------------------

def test_modern_professional_agency_does_not_force_dark():
    prompt = "modern professional agency website"
    modes = [choose_palette_hint(prompt, salt=str(i))["mode"] for i in range(200)]
    assert modes.count("light") > modes.count("dark")
    assert "light" in modes


def test_planner_prompt_no_longer_maps_style_words_to_dark():
    # The old keyword table mapped these style words straight to dark mode.
    assert '"dark", "elegant", "luxury", "professional", "sleek", "modern"' not in PLANNER_SYSTEM_PROMPT
    assert "Dark Theme:" not in PLANNER_SYSTEM_PROMPT and "Dark Financial" not in PLANNER_SYSTEM_PROMPT
    assert "do NOT imply dark mode" in PLANNER_SYSTEM_PROMPT
    for name in PALETTES:
        assert f"- {name}:" in PLANNER_SYSTEM_PROMPT


def test_hint_is_deterministic_per_salt_and_varies_across_salts():
    prompt = "landing page for a coffee roastery"
    assert choose_palette_hint(prompt, salt="abc") == choose_palette_hint(prompt, salt="abc")
    palettes = {choose_palette_hint(prompt, salt=str(i))["palette"] for i in range(60)}
    assert len(palettes) >= 3
    # Default (no salt) is randomised per request.
    assert len({choose_palette_hint(prompt)["palette"] for _ in range(40)}) >= 2


def test_hint_follows_subject():
    for i in range(30):
        assert choose_palette_hint("online pet store for dog toys", salt=str(i))["palette"] in {"candy", "earth", "citrus", "sunset"}
        assert choose_palette_hint("yoga studio class schedule", salt=str(i))["palette"] in {"forest", "earth", "ocean", "berry"}


@pytest.mark.parametrize("text,keyword,expected", [
    ("pets and vets", "pet", True), ("carpet cleaning", "pet", False),
    ("an ai startup", "ai", True), ("email marketing", "ai", False), ("barber shop", "bar", False),
])
def test_keyword_matching_is_word_based(text, keyword, expected):
    assert llm._mentions(f" {text} ", keyword) is expected


def test_explicit_mode_words_win():
    assert all(choose_palette_hint("a dark mode crypto dashboard", salt=str(i))["mode"] == "dark" for i in range(20))
    assert all(choose_palette_hint("bright and airy bakery site", salt=str(i))["mode"] == "light" for i in range(20))


# --------------------------------------------------------------------------
# normalize_color_scheme
# --------------------------------------------------------------------------

HINT = {"palette": "ocean", "mode": "light", "reason": "test"}


def test_normalize_fills_missing_theme_from_hint():
    plan = {"project_name": "x"}
    scheme = normalize_color_scheme(plan, HINT)
    assert plan["theme"]["color_scheme"] is scheme
    assert scheme == build_color_scheme("ocean", "light")


def test_normalize_uses_planner_palette_over_hint():
    plan = {"theme": {"color_scheme": {"palette": "forest", "mode": "dark"}}}
    assert normalize_color_scheme(plan, HINT) == build_color_scheme("forest", "dark")


def test_normalize_keeps_custom_user_colours_and_fixes_contrast():
    plan = {"theme": {"color_scheme": {
        "palette": "custom", "mode": "light", "background": "#fde2e4", "primary": "#e63946",
        "accent": "not-a-colour", "text": "#fefefe",  # unreadable text on a light background
    }}}
    s = normalize_color_scheme(plan, HINT)
    assert s["palette"] == "custom"
    assert s["background"] == "#fde2e4" and s["primary"] == "#e63946"
    assert HEX.match(s["accent"])  # invalid value replaced from the hint palette
    assert contrast_ratio(s["text"], s["background"]) >= 4.5
    assert s["hero"][0] == "#e63946"  # derived from the custom colours, not ocean's
    # A mid-tone custom colour can't reach 4.5:1 with either white or near-black;
    # the better one is chosen (fine for bold button / large hero text).
    best = max(contrast_ratio(c, s["primary"]) for c in (llm.LIGHT_TEXT, llm.DARK_TEXT))
    assert contrast_ratio(s["on_primary"], s["primary"]) == best >= 3


@pytest.mark.parametrize("legacy_mode,background,expected", [
    ("vibrant", "#667eea", "light"), ("soft", "#ede9fe", "light"), ("dark", "#0a0a0a", "dark"), (None, "#0f172a", "dark"),
])
def test_normalize_maps_legacy_modes(legacy_mode, background, expected):
    plan = {"theme": {"color_scheme": {"mode": legacy_mode, "background": background}}}
    assert normalize_color_scheme(plan, HINT)["mode"] == expected


# --------------------------------------------------------------------------
# (b) stage-2 prompt carries the planner's hex values as arbitrary classes
# --------------------------------------------------------------------------

def plan_with(scheme):
    return {"project_name": "Paws", "project_description": "Pet shop", "theme": {"style": "playful", "color_scheme": scheme}}


def test_stage2_prompt_includes_planner_hex_as_arbitrary_classes():
    client = LLMClient(ui_model_id="groq:openai/gpt-oss-20b")
    plan = plan_with({})
    normalize_color_scheme(plan, {"palette": "candy", "mode": "light"})
    s = plan["theme"]["color_scheme"]
    text = client._build_ui_request("SECTIONS...", plan)
    assert f"bg-[{s['background']}]" in text
    assert f"from-[{s['hero'][0]}] to-[{s['hero'][1]}]" in text
    assert f"bg-[{s['primary']}] text-[{s['on_primary']}]" in text
    assert f"bg-[{s['accent']}]" in text
    assert "pink" in text and "fuchsia" in text  # palette families for secondary elements
    assert "Worked example" in text
    assert "SECTIONS..." in text


def test_stage2_prompt_uses_custom_planner_hex():
    client = LLMClient(ui_model_id="groq:openai/gpt-oss-20b")
    plan = plan_with({"palette": "custom", "mode": "dark", "background": "#101820", "primary": "#fee715",
                      "surface": "#1b2836", "secondary": "#f2aa4c", "accent": "#00a6a6"})
    normalize_color_scheme(plan, HINT)
    text = client._build_ui_request("", plan)
    for hexval in ("#101820", "#fee715", "#1b2836", "#00a6a6"):
        assert f"[{hexval}]" in text


def test_stage2_prompt_repairs_unnormalised_plan():
    client = LLMClient(ui_model_id="groq:openai/gpt-oss-20b")
    text = client._build_ui_request("", {"theme": {"color_scheme": {"mode": "vibrant", "primary": "#ec4899"}}})
    assert "bg-[#ec4899]" in text


def test_ui_system_prompt_examples_have_no_white_or_pale_backgrounds():
    examples = UI_GENERATOR_SYSTEM_PROMPT[UI_GENERATOR_SYSTEM_PROMPT.index("MODERN UI PATTERNS"):]
    for pale in ("bg-white", "from-white", "via-white", "to-white", "from-gray-50", "purple-50", "blue-50", "amber-50"):
        assert pale not in examples, pale
    assert "Text should never have white color" not in UI_GENERATOR_SYSTEM_PROMPT


def test_colour_guidance_dark_uses_dark_family_shades():
    g = colour_guidance(build_color_scheme("neon", "dark"))
    assert "bg-cyan-900 text-cyan-200" in g and "mode: dark" in g


# --------------------------------------------------------------------------
# Token resolution and generate_ui wiring
# --------------------------------------------------------------------------

def test_resolve_color_tokens():
    s = build_color_scheme("ocean", "light")
    schema = {"type": "Root", "props": {"className": "bg-[{{background}}] text-[{{ text }}]"}, "children": [
        {"type": "Hero", "props": {"className": "from-[{{hero_from}}] to-[{{hero_to}}] {{unknown}}"}},
        "plain string child",
    ]}
    resolve_color_tokens(schema, s)
    assert schema["props"]["className"] == f"bg-[{s['background']}] text-[{s['text']}]"
    assert schema["children"][0]["props"]["className"] == f"from-[{s['hero'][0]}] to-[{s['hero'][1]}] {{{{unknown}}}}"


@patch("generation.llm.LLMClient._call_ui_generator")
@patch("generation.llm.LLMClient._call_planner")
def test_generate_ui_sends_hint_normalises_and_resolves_tokens(mock_planner, mock_ui):
    mock_planner.return_value = {"project_name": "P", "project_description": "D", "theme": {"color_scheme": {"palette": "berry", "mode": "light"}}}
    mock_ui.return_value = {"title": "T", "schema": {"type": "Root", "props": {"className": "bg-[{{background}}]"}}, "metadata": {}}

    result = LLMClient(ui_model_id="groq:openai/gpt-oss-20b").generate_ui("site for a jazz club")

    planner_prompt = mock_planner.call_args.args[0]
    assert planner_prompt.startswith("site for a jazz club") and "PALETTE HINT" in planner_prompt
    scheme = result["design_plan"]["theme"]["color_scheme"]
    assert scheme == build_color_scheme("berry", "light")
    assert result["schema"]["props"]["className"] == f"bg-[{scheme['background']}]"


# --------------------------------------------------------------------------
# Temperatures
# --------------------------------------------------------------------------

def test_default_temperatures():
    client = LLMClient(ui_model_id="groq:openai/gpt-oss-20b")
    assert client.ui_temperature == 0.65
    assert client.planner_temperature == 0.4


def test_temperatures_configurable_and_clamped(settings, monkeypatch):
    settings.LLM_UI_TEMPERATURE = "0.9"
    monkeypatch.setenv("LLM_PLANNER_TEMPERATURE", "7")
    client = LLMClient(ui_model_id="groq:openai/gpt-oss-20b")
    assert client.ui_temperature == 0.9
    assert client.planner_temperature == 1.5
    settings.LLM_UI_TEMPERATURE = "garbage"
    assert LLMClient(ui_model_id="groq:openai/gpt-oss-20b").ui_temperature == 0.65


@patch("generation.llm.requests.post")
def test_ui_stage_sends_ui_temperature(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"choices": [{"message": {"content": '{"title": "t", "schema": {}, "metadata": {}}'}}]}
    client = LLMClient(ui_model_id="groq:openai/gpt-oss-20b")
    client._call_ui_generator("x", plan_with({}), retries=1)
    assert mock_post.call_args.kwargs["json"]["temperature"] == 0.65


# --------------------------------------------------------------------------
# (c) codegen: no white-to-white rewrite; coloured, theme-aware defaults
# --------------------------------------------------------------------------

def gen(schema, theme=None):
    return ReactCodeGenerator(copy.deepcopy(schema), theme=theme).generate()


@pytest.mark.parametrize("node_type", ["Root", "Card", "Hero", "Timeline", "TimelineItem", "Section"])
def test_bg_white_is_not_rewritten_to_white_gradient(node_type):
    out = gen({"type": node_type, "props": {"className": "bg-white p-4"}, "children": []})
    assert "from-white to-gray-50" not in out
    assert "via-white" not in out
    assert "bg-white p-4" in out


def test_default_hero_and_timeline_are_coloured_without_theme():
    out = gen({"type": "Root", "children": [
        {"type": "Hero", "children": [{"type": "Text", "content": "Hi"}]},
        {"type": "Timeline", "children": [{"type": "TimelineItem", "children": [{"type": "Text", "content": "2020"}]}]},
    ]})
    assert "bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white rounded-2xl shadow-lg p-12" in out
    assert "border-indigo-400" in out and "bg-indigo-50 border-l-4 border-pink-500" in out and "bg-pink-500" in out
    assert "from-blue-50" not in out and "from-white" not in out
    # Root without a theme gets no colour, only the full-viewport height.
    assert '<main className="min-h-screen">' in out


def test_defaults_derive_from_theme():
    scheme = build_color_scheme("sunset", "light")
    out = gen({"type": "Root", "children": [
        {"type": "Hero", "children": []},
        {"type": "Timeline", "children": [{"type": "TimelineItem", "children": []}]},
    ]}, theme={"style": "warm", "color_scheme": scheme})
    assert f'<main className="bg-[{scheme["background"]}] text-[{scheme["text"]}] min-h-screen">' in out
    assert f"from-[{scheme['hero'][0]}] to-[{scheme['hero'][1]}] text-[{scheme['on_hero']}]" in out
    assert f"border-[{scheme['primary']}]" in out
    assert f"bg-[{scheme['surface']}] border-l-4 border-[{scheme['accent']}]" in out
    assert f"bg-[{scheme['accent']}] rounded-full" in out


def test_explicit_classes_beat_theme_defaults():
    scheme = build_color_scheme("forest", "dark")
    out = gen({"type": "Root", "props": {"className": "bg-[#123456]"}, "children": [
        {"type": "Hero", "props": {"className": "bg-[#abcdef] rounded-xl"}, "children": []}]}, theme=scheme)
    assert scheme["background"] not in out.split("bg-[#123456]")[0]
    assert '<div className="bg-[#abcdef] rounded-xl">' in out


def test_invalid_theme_values_are_ignored():
    out = gen({"type": "Root", "children": [{"type": "Hero", "children": []}]},
              theme={"background": '#fff"] onClick={x}', "primary": "red", "hero": ["#000", "javascript:"], "accent": "#zzzzzz"})
    assert "onClick" not in out and "javascript" not in out
    assert "from-indigo-500 via-purple-500 to-pink-500" in out


def test_render_schema_accepts_theme():
    scheme = build_color_scheme("midnight", "light")
    assert f"bg-[{scheme['background']}]" in render_schema({"type": "Root"}, theme=scheme)
    assert render_schema({"type": "Root"}) == ReactCodeGenerator({"type": "Root"}).generate()


# ---------------------------------------------------------------------------
# Stage-2 prompt must not contradict the COLOUR SYSTEM
# ---------------------------------------------------------------------------

def _stage2_request(typography=None, style="warm minimal clean"):
    from generation.llm import LLMClient, normalize_color_scheme
    plan = {"project_name": "Bakery", "project_description": "d", "intent": "i",
            "theme": {"style": style, "color_scheme": {"palette": "sunset", "mode": "dark"}, "typography": typography or {}},
            "design_plan": {"sections": [{"name": "Hero", "type": "hero", "content": "x"}]}}
    normalize_color_scheme(plan, {"palette": "sunset", "mode": "dark"})
    client = LLMClient.__new__(LLMClient)
    return client._build_ui_request(client._compile_ui_prompt(plan), plan)


def test_planner_typography_colours_are_stripped_from_the_prompt():
    out = _stage2_request({"heading": "text-4xl font-bold text-gray-900 hover:text-[#111]", "body": "text-base text-slate-600/80 leading-7"})
    assert "Hero: text-4xl font-bold, Body: text-base leading-7" in out
    assert "text-gray-900" not in out and "slate-600" not in out


def test_strip_colour_classes_keeps_sizes_and_weights():
    from generation.llm import strip_colour_classes
    assert strip_colour_classes("text-xs text-sm text-2xl text-center font-semibold tracking-tight") == "text-xs text-sm text-2xl text-center font-semibold tracking-tight"
    assert strip_colour_classes("text-white bg-black border-[#fff] from-red-500") == ""
    assert strip_colour_classes(None) == "" and strip_colour_classes(["x"]) == ""


def test_stage2_prompt_has_no_instructions_that_push_towards_plain_pages():
    from generation.llm import UI_GENERATOR_SYSTEM_PROMPT
    out = _stage2_request()
    assert "optional background" not in out
    assert "never colour" in out  # style words like "minimal" are not colour instructions
    # shadcn tokens and v3 opacity helpers render with no colour in the preview:
    # they may be named once, in the rule that forbids them, and in no example.
    assert UI_GENERATOR_SYSTEM_PROMPT.count("text-muted-foreground") == 1
    assert UI_GENERATOR_SYSTEM_PROMPT.count("bg-opacity") == 1
    assert "muted-foreground" not in out and "bg-opacity" not in out
