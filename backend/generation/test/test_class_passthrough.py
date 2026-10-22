"""
CSS classes are NOT part of the safety layer, and must never be changed by it.

A page's colours are nothing but classes (bg-[#0f172a], from-indigo-500, hover:...,
bg-blue-500/50), so anything that filters, rewrites or "fixes" them shows up as a
white or plain site. What keeps a hostile className from doing damage is codegen's
escaping (jsx_attr), and the WebContainer origin boundary: see "Security model" in
the README. These tests pin that down:

  * validator: className out == className in (whitespace collapsed)
  * codegen: every class in the schema appears, unchanged and in order, in the
    generated source, for every node type and every render path
  * nobody re-adds a whitelist/allowlist/denylist of classes
  * theme defaults only ever ADD classes, and a re-render gives the same code as
    the first generation
"""
import ast
import copy
import json
import random
import re
from pathlib import Path

import pytest

from generation import cache as generation_cache
from generation import codegen as codegen_module
from generation import schema_validator as validator_module
from generation.codegen import ReactCodeGenerator, apply_theme_defaults, render_schema
from generation.llm import LLMClient, build_color_scheme, resolve_color_tokens
from generation.schema_validator import SchemaValidator

THEME = {"style": "bold", "color_scheme": build_color_scheme("midnight", "dark")}

# ---------------------------------------------------------------------------
# Corpus: ~220 className strings of the kind models actually write.
# ---------------------------------------------------------------------------

HAND_WRITTEN = [
    # gradients, v3 and v4 spellings, arbitrary stops
    "bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white rounded-2xl shadow-lg p-12",
    "bg-gradient-to-r from-[#667eea] to-[#764ba2]",
    "bg-linear-to-br from-sky-400 to-blue-600",
    "bg-gradient-to-tl from-[#0369a1] via-[#38bdf8]/60 to-[#1d4ed8] text-[#f8fafc]",
    "bg-gradient-to-b from-transparent to-black/60",
    "bg-[linear-gradient(135deg,#667eea_0%,#764ba2_100%)]",
    "bg-[radial-gradient(circle_at_top,#1e293b,#0f172a)]",
    # arbitrary hex / functional colours
    "bg-[#0f172a] text-[#f8fafc]",
    "text-[#fbbf24] border-[#fbbf24]/40 border",
    "bg-[#fff] bg-[#ffffff] bg-[#FFFFFFAA]",
    "bg-[rgb(15,23,42)] text-[hsl(48,96%,53%)] border-[oklch(0.7_0.15_250)]",
    "bg-[color:var(--brand)] text-[color:var(--ink)]",
    "ring-2 ring-[#fbbf24] ring-offset-2 ring-offset-[#0f172a]",
    "shadow-[0_10px_40px_-10px_#6366f1] shadow-indigo-500/50",
    "fill-[#e11d48] stroke-[#0f172a] accent-[#ec4899] caret-[#f43f5e]",
    "decoration-[#fbbf24] underline decoration-wavy",
    "divide-y divide-[#334155]/50",
    "placeholder:text-[#94a3b8] focus:ring-[#fbbf24] focus:border-[#fbbf24]",
    # opacity colours
    "bg-blue-500/50 text-white/80 border-white/10",
    "bg-black/[.08] bg-white/[0.12]",
    "bg-[#0f172a]/90 text-[#cbd5e1]/80 border-[#334155]/40",
    # variants
    "hover:bg-[#1d4ed8] hover:text-white hover:-translate-y-1 transition",
    "md:bg-rose-600 lg:bg-[#e11d48] sm:text-xl xl:p-16 2xl:max-w-screen-2xl",
    "dark:bg-[#020617] dark:text-yellow-300 dark:hover:bg-slate-800",
    "group-hover:bg-rose-100 group-hover:text-rose-900 peer-checked:bg-emerald-500",
    "first:pt-0 last:pb-0 odd:bg-gray-50 even:bg-gray-100 focus-visible:ring-2 active:scale-95",
    "disabled:opacity-50 disabled:cursor-not-allowed aria-selected:bg-[#fbbf24]",
    "data-[state=open]:bg-red-500 aria-[sort=ascending]:text-[#fbbf24] supports-[display:grid]:grid",
    "max-md:hidden min-[900px]:flex @container @lg:flex @md:grid-cols-2",
    "motion-safe:animate-pulse motion-reduce:transition-none print:hidden",
    "has-[:checked]:bg-indigo-50 not-first:mt-4 in-[.dark]:text-white nth-[3n+1]:bg-slate-100",
    # arbitrary variants, important, negatives, groups
    "[&>*]:p-2 [&_svg]:size-4 [&:nth-child(2)]:bg-[#fbbf24] [&_p]:text-[#e2e8f0]",
    "!bg-black !text-white !font-bold bg-red-500! text-lg!",
    "-mt-4 -translate-x-1/2 -rotate-6 -z-10 -inset-x-4 -space-x-2",
    "group group/item peer peer/name group-hover/item:underline",
    # arbitrary values with quotes / backslashes / entities: these take codegen's JSON-literal branch
    "before:content-[''] after:content-['\"'] after:content-[\"\\201C\"]",
    "font-['Inter',sans-serif] font-[\"Playfair_Display\"]",
    "bg-[url('/hero.png')] bg-[url(\"/hero.png\")]",
    "before:content-['&amp;'] after:content-['&#8226;'] before:content-['&quot;']",
    "[&>a[href^='http']]:underline [&_a[href$=\".pdf\"]]:text-[#e11d48]",
    # layout and sizing
    "grid grid-cols-1 md:grid-cols-3 gap-6 lg:grid-cols-[1fr_2fr] auto-rows-[minmax(0,1fr)]",
    "w-[calc(100%-2rem)] h-[50vh] min-h-[320px] max-w-[1200px] aspect-[16/9] top-[117px]",
    "flex flex-col items-center justify-between gap-x-4 gap-y-[18px] space-y-8",
    "relative absolute inset-0 z-[60] overflow-hidden object-cover",
    "text-[clamp(2rem,5vw,4rem)] leading-[1.1] tracking-[-0.02em] font-[800]",
    "container mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-20",
    "sticky top-0 backdrop-blur-md bg-[#0f172a]/80 border-b border-white/10",
    "line-clamp-3 truncate whitespace-nowrap uppercase italic underline-offset-4",
    "animate-[spin_3s_linear_infinite] transition-[background-color,transform] duration-[400ms]",
    "[mask-image:linear-gradient(to_bottom,black,transparent)] [--brand:#fbbf24]",
    "origin-[50%_0] rotate-[17deg] scale-[1.02] translate-y-[-2px] skew-x-3",
    # things that are not Tailwind at all must pass through too
    "btn btn-primary custom-card my-widget--active __weird__ prose prose-lg",
    "bg-brand-500 text-brand-100 border-brand-300 font-display",
    "zz-not-a-utility-9000 x:y:z:bg-red-500 bg-#123456 text-[red",
]

_LAYOUT = ["flex", "grid", "relative", "w-full", "min-h-screen", "p-6", "px-4", "py-12", "gap-6", "mx-auto", "max-w-7xl",
           "items-center", "justify-center", "rounded-xl", "rounded-2xl", "shadow-md", "shadow-lg", "overflow-hidden",
           "text-center", "text-5xl", "text-sm", "font-bold", "font-semibold", "leading-tight", "tracking-tight",
           "sm:grid-cols-2", "md:flex-row", "lg:px-8", "space-y-4", "col-span-2", "z-10", "transition-all", "duration-300"]
_COLOUR = ["bg-slate-900", "bg-rose-600", "bg-emerald-500", "bg-[#0369a1]", "bg-[#fbbf24]", "bg-white", "bg-black/50", "bg-amber-100/80",
           "text-white", "text-slate-100", "text-[#fbbf24]", "text-rose-900", "text-[#0f172a]/80", "text-transparent",
           "border-[#334155]", "border-rose-300", "border-white/20", "ring-indigo-500", "from-[#0369a1]", "via-[#38bdf8]",
           "to-[#1d4ed8]", "from-indigo-500", "via-purple-500", "to-pink-500", "bg-gradient-to-br", "bg-gradient-to-r",
           "bg-linear-to-t", "bg-clip-text", "shadow-indigo-500/40", "fill-current", "stroke-[#e11d48]", "bg-opacity-50"]
_VARIANT = ["hover:", "focus:", "md:", "lg:", "dark:", "group-hover:", "sm:", "active:", "disabled:", "[&>*]:", "peer-checked:", "data-[open]:"]
_EXTRA = ["-mt-2", "-translate-y-1", "!p-0", "p-2!", "w-[37px]", "content-['x']", "font-['Inter']", "before:content-[\"y\"]", "[&_a]:underline"]


def _generated_corpus(count: int = 150, seed: int = 20260622):
    rng = random.Random(seed)
    out = []
    for _ in range(count):
        tokens = rng.sample(_LAYOUT, rng.randint(2, 6)) + rng.sample(_COLOUR, rng.randint(1, 4))
        tokens += [rng.choice(_VARIANT) + rng.choice(_COLOUR) for _ in range(rng.randint(0, 3))]
        tokens += rng.sample(_EXTRA, rng.randint(0, 2))
        rng.shuffle(tokens)
        out.append(" ".join(tokens))
    return out


CORPUS = HAND_WRITTEN + _generated_corpus()


def normalised(class_name: str) -> str:
    """The one thing the validator may do: collapse whitespace."""
    return " ".join(class_name.split())


# Node types, and how each renders its className (so every code path is covered).
LEAF_TYPES = ["Root", "Section", "Container", "Grid", "Flex", "Div", "Card", "CardHeader", "CardContent", "CardFooter",
              "CardTitle", "CardDescription", "Hero", "Timeline", "TimelineItem", "Text", "Button", "Link", "Link/A",
              "Image", "Icon", "Input", "Badge", "Label", "Separator", "List", "ListItem", "Form", "Table", "TableRow",
              "TableCell", "TableHead", "span", "div", "section", "unknown-type", "Mystery"]

ATTR = re.compile(r"""className=(?:"([^"]*)"|'([^']*)'|\{("(?:[^"\\]|\\.)*")\})""")


def class_attributes(code: str):
    """Every className in the generated source, decoded the way JSX/JS would."""
    return [m.group(1) if m.group(1) is not None else m.group(2) if m.group(2) is not None else json.loads(m.group(3))
            for m in ATTR.finditer(code)]


def assert_class_present(code: str, wanted: str):
    """`wanted` appears unchanged and in order at the start of some className
    (theme defaults, if any, come after it)."""
    attrs = class_attributes(code)
    assert any(a == wanted or a.startswith(wanted + " ") for a in attrs), (
        f"className {wanted!r} did not survive codegen; got {attrs}")


def node(node_type: str, class_name):
    return {"type": node_type, "props": {"className": class_name}, "content": "x"}


# ---------------------------------------------------------------------------
# validator
# ---------------------------------------------------------------------------

def test_corpus_size_and_variety():
    assert len(CORPUS) >= 200
    assert len(set(CORPUS)) == len(CORPUS)


@pytest.mark.parametrize("classes", CORPUS)
def test_validator_returns_classname_unchanged(classes):
    for node_type in ("Root", "Hero", "Card", "Text", "Button"):
        out = SchemaValidator.validate(node(node_type, classes))["props"]["className"]
        assert out == normalised(classes)


def test_validator_collapses_only_whitespace_and_control_characters():
    out = SchemaValidator.validate(node("Card", "  bg-[#0f172a]\n\ttext-white\x00hover:bg-red-500\x1b  "))["props"]["className"]
    assert out == "bg-[#0f172a] text-white hover:bg-red-500"


def test_validator_does_not_touch_other_props_while_cleaning_classname():
    schema = {"type": "Button", "props": {"className": "bg-[#fbbf24]", "variant": "outline", "disabled": 1}}
    assert SchemaValidator.validate(schema)["props"] == {"className": "bg-[#fbbf24]", "variant": "outline", "disabled": True}


# ---------------------------------------------------------------------------
# codegen: every node type, every corpus string, with and without a theme
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("classes", CORPUS)
@pytest.mark.parametrize("theme", [None, THEME], ids=["no-theme", "theme"])
def test_codegen_emits_every_class_unchanged_for_every_node_type(classes, theme):
    schema = {"type": "Root", "props": {"className": classes}, "children": [node(t, classes) for t in LEAF_TYPES]}
    validated = SchemaValidator.validate(copy.deepcopy(schema))
    code = ReactCodeGenerator(validated, theme=theme).generate()
    wanted = normalised(classes)
    attrs = class_attributes(code)
    # Root + one className per node type (TimelineItem also emits a dot, inline text a span)
    assert sum(1 for a in attrs if a == wanted or a.startswith(wanted + " ")) >= 1 + len(LEAF_TYPES) - 1
    assert_class_present(code, wanted)


@pytest.mark.parametrize("classes", CORPUS[::4])
def test_codegen_emits_classes_of_inline_and_nested_nodes(classes):
    schema = {"type": "Root", "children": [
        {"type": "Text", "props": {"tag": "h1", "className": "text-4xl"}, "children": [
            {"type": "Text", "props": {"className": classes}, "content": "inline"},
            {"type": "span", "props": {"className": classes}, "content": "span"},
            "tail",
        ]},
        {"type": "Section", "children": [{"type": "Grid", "children": [{"type": "Card", "children": [node("Text", classes)]}]}]},
    ]}
    code = render_schema(schema)
    assert sum(1 for a in class_attributes(code) if a == normalised(classes)) >= 3


@pytest.mark.parametrize("classes", CORPUS)
def test_classes_survive_the_whole_chain(classes):
    """raw model JSON -> _parse_response -> colour tokens -> validate -> theme defaults -> codegen -> re-render."""
    schema = {"type": "Root", "props": {"className": classes}, "children": [node("Hero", classes), node("Card", classes)]}
    client = LLMClient.__new__(LLMClient)
    parsed = client._parse_response("```json\n" + json.dumps({"schema": schema}, indent=2) + "\n```", {})["schema"]
    resolve_color_tokens(parsed, THEME["color_scheme"])
    validated = SchemaValidator.validate(parsed)
    assert validated["props"]["className"] == normalised(classes)

    baked = apply_theme_defaults(copy.deepcopy(validated), THEME)
    for n in (baked, *baked["children"]):
        assert n["props"]["className"].startswith(normalised(classes))

    first = ReactCodeGenerator(baked, theme=THEME).generate()
    assert_class_present(first, normalised(classes))
    # A re-render without the theme (project detail, version history, patch save)
    # produces exactly the same source as the first generation.
    assert render_schema(baked) == first
    assert render_schema(baked, theme=THEME) == first


def test_color_tokens_are_the_only_rewrite_and_only_for_known_names():
    scheme = THEME["color_scheme"]
    schema = {"type": "Root", "props": {"className": "bg-[{{background}}] text-[{{ text }}] bg-[{{nope}}] bg-[#123456]"}}
    resolve_color_tokens(schema, scheme)
    assert schema["props"]["className"] == f"bg-[{scheme['background']}] text-[{scheme['text']}] bg-[{{{{nope}}}}] bg-[#123456]"


# ---------------------------------------------------------------------------
# property style: arbitrary class-shaped strings
# ---------------------------------------------------------------------------

_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789-_/:.[]#%!&>*()=,~+@'\"\\"


def _random_tokens(rng, n):
    return " ".join("".join(rng.choice(_ALPHABET) for _ in range(rng.randint(1, 14))) for _ in range(n))


def test_random_class_shaped_strings_round_trip():
    rng = random.Random(1234)
    for _ in range(600):
        classes = _random_tokens(rng, rng.randint(1, 8))
        out = SchemaValidator.validate(node("Div", classes))["props"]["className"]
        assert out == normalised(classes)
        code = ReactCodeGenerator({"type": "Div", "props": {"className": out}, "children": []}).generate()
        assert class_attributes(code) == [out], classes


# ---------------------------------------------------------------------------
# nobody re-adds a whitelist
# ---------------------------------------------------------------------------

def test_unknown_and_future_utilities_are_not_filtered():
    """A whitelist would drop these: names no list could know about."""
    made_up = "bg-future-utility-2031 from-[#123456] custom-brand-class text-[#abcdef]/37 zz-9000 bg-quantum-950"
    schema = {"type": "Root", "children": [node(t, made_up) for t in ("Section", "Card", "Hero", "Button", "Text")]}
    out = SchemaValidator.validate(copy.deepcopy(schema))
    assert all(c["props"]["className"] == made_up for c in out["children"])
    code = render_schema(schema)
    assert sum(1 for a in class_attributes(code) if a.startswith(made_up)) == 5


def test_classname_length_limit_is_the_only_size_cap_and_cuts_at_a_class_boundary():
    classes = " ".join(f"bg-[#{i:06x}]" for i in range(400))
    out = SchemaValidator.validate(node("Div", classes))["props"]["className"]
    assert len(out) <= validator_module.MAX_CLASSNAME_LENGTH
    assert out == " ".join(classes.split()[: len(out.split())])  # a prefix, whole classes only


_FILTER_NAME = re.compile(r"(class|css|tailwind|utilit).*(allow|white|black|deny|safe|permit|valid|pattern|prefix|regex)"
                          r"|(allow|white|black|deny|safe|permit|valid|pattern|prefix|regex).*(class|css|tailwind|utilit)", re.I)


@pytest.mark.parametrize("module", [validator_module, codegen_module, generation_cache])
def test_no_class_filter_constants_or_helpers_in_the_safety_layer(module):
    """Names that look like a class allow/deny list (ALLOWED_CLASSES, CLASS_PATTERN,
    SAFE_CSS_PREFIXES, sanitize_classes...) are what re-introducing a whitelist
    looks like. Read-only inspection helpers (has_background...) are fine."""
    tree = ast.parse(Path(module.__file__).read_text())
    names = []
    for item in ast.walk(tree):
        if isinstance(item, (ast.FunctionDef, ast.ClassDef)):
            names.append(item.name)
        elif isinstance(item, ast.Assign):
            names += [t.id for t in item.targets if isinstance(t, ast.Name)]
    offenders = [n for n in names if _FILTER_NAME.search(n) and n not in {"_clean_classname"}]
    assert offenders == []


def test_validate_classname_cleaning_is_whitespace_only():
    source = Path(validator_module.__file__).read_text()
    body = source[source.index("def _clean_classname"):source.index("def enforce_fixed_image")]
    # Only these regex/operations may touch a className; no per-class tests.
    assert "_CONTROL_CHARS.sub" in body and ".split()" in body
    for forbidden in ("re.match", "re.search", "re.fullmatch", "startswith", " in ALLOWED", "for cls in", "for c in classname.split"):
        assert forbidden not in body, forbidden


# ---------------------------------------------------------------------------
# theme defaults: additive, idempotent, consistent across render paths
# ---------------------------------------------------------------------------

def _gen(theme=None):
    return ReactCodeGenerator({}, theme=theme)


@pytest.mark.parametrize("classes", CORPUS)
@pytest.mark.parametrize("node_type", ["Root", "Hero", "Timeline", "TimelineItem", "Card", "Section"])
def test_theme_defaults_only_add_and_are_idempotent(classes, node_type):
    gen = _gen(THEME)
    once = gen.with_defaults(node_type, normalised(classes))
    assert once.startswith(normalised(classes))
    assert gen.with_defaults(node_type, once) == once


@pytest.mark.parametrize("class_name", ["hover:bg-red-500", "dark:bg-slate-900", "md:bg-[#fff]", "bg-clip-text text-transparent", "bg-cover bg-center"])
def test_variant_and_non_colour_bg_utilities_do_not_count_as_a_background(class_name):
    gen = _gen(THEME)
    colours = THEME["color_scheme"]
    assert f"bg-[{colours['background']}]" in gen.with_defaults("Root", class_name)
    assert f"bg-[{colours['surface']}]" in gen.with_defaults("Card", class_name)
    assert "from-[" in gen.with_defaults("Hero", class_name)


@pytest.mark.parametrize("class_name", ["bg-red-500", "bg-[#0f172a]", "bg-gradient-to-br from-a to-b", "bg-linear-to-r", "!bg-black", "bg-white/10", "p-4 bg-slate-900!"])
def test_a_real_background_is_never_overridden_by_a_default(class_name):
    gen = _gen(THEME)
    for node_type in ("Root", "Card", "TimelineItem"):
        out = gen.with_defaults(node_type, class_name)
        added = out[len(class_name):].split()
        assert not any(t.startswith("bg-") for t in added), (node_type, out)
    assert "from-[" not in gen.with_defaults("Hero", class_name)


def test_root_default_brings_matching_text_colour_only_with_its_own_background():
    colours = THEME["color_scheme"]
    bare = _gen(THEME).with_defaults("Root", "min-h-screen")
    assert bare == f"min-h-screen bg-[{colours['background']}] text-[{colours['text']}]"
    # The model chose its own background: the theme's text colour was checked against a different one.
    assert _gen(THEME).with_defaults("Root", "bg-[#fff7ed] min-h-screen") == "bg-[#fff7ed] min-h-screen"
    assert _gen(THEME).with_defaults("Root", "text-rose-900") == f"text-rose-900 bg-[{colours['background']}] min-h-screen"


def test_root_always_fills_the_viewport_so_its_background_does_not_stop_halfway():
    assert _gen().with_defaults("Root", "") == "min-h-screen"
    assert _gen().with_defaults("Root", "bg-red-500 min-h-[80vh]") == "bg-red-500 min-h-[80vh]"
    assert _gen().with_defaults("Root", "md:min-h-screen min-h-0") == "md:min-h-screen min-h-0"  # explicit min-h- wins
    assert _gen().with_defaults("Root", "md:min-h-screen") == "md:min-h-screen min-h-screen"  # a variant is not a base height


def test_apply_theme_defaults_makes_a_stored_schema_render_like_the_first_generation():
    """The bug this guards: first generation got the theme's page background and
    hero gradient, but every later render (project reopen, version, patch save,
    edit mode) rebuilt the code without the theme and came out plain."""
    schema = {"type": "Root", "props": {"className": "min-h-screen"}, "children": [
        {"type": "Hero", "props": {"className": "p-12"}, "children": []},
        {"type": "Section", "children": [{"type": "Card", "children": []}]},
        {"type": "Timeline", "children": [{"type": "TimelineItem", "children": []}]},
    ]}
    first = ReactCodeGenerator(copy.deepcopy(schema), theme=THEME).generate()
    reopened_without_fix = render_schema(copy.deepcopy(schema))
    assert reopened_without_fix != first  # a schema that was never baked loses the theme

    baked = apply_theme_defaults(copy.deepcopy(schema), THEME)
    assert render_schema(baked) == first
    colours = THEME["color_scheme"]
    assert baked["props"]["className"].startswith("min-h-screen")
    assert f"bg-[{colours['background']}]" in baked["props"]["className"]
    assert f"from-[{colours['hero'][0]}]" in baked["children"][0]["props"]["className"]
    assert f"bg-[{colours['surface']}]" in baked["children"][1]["children"][0]["props"]["className"]


def test_apply_theme_defaults_tolerates_malformed_nodes():
    schema = {"type": "Root", "props": None, "children": ["text", None, 5, {"type": 7}, {"type": "Card", "props": "bad"}, {"type": "Hero"}]}
    apply_theme_defaults(schema, THEME)
    assert "bg-[" in schema["props"]["className"]
    assert "from-[" in schema["children"][-1]["props"]["className"]
    assert schema["children"][4]["props"] == "bad"


# ---------------------------------------------------------------------------
# every re-render path passes the generation's theme
# ---------------------------------------------------------------------------

BARE_SCHEMA = {"type": "Root", "props": {"className": "min-h-screen"}, "children": [
    {"type": "Hero", "props": {"className": "p-12"}, "children": [{"type": "Text", "content": "Hi"}]}]}


@pytest.fixture
def themed_generation(user, db):
    from generation.models import Generations
    from projects.models import Project
    project = Project.objects.create(user=user, title="Proj", description="")
    return Generations.objects.create(
        project=project, prompt="hi", schema=copy.deepcopy(BARE_SCHEMA), llm_provider="groq", status="success",
        metadata={"theme": THEME, "design_plan": {"theme": THEME}},
    )


def _assert_themed(code):
    colours = THEME["color_scheme"]
    assert f"bg-[{colours['background']}]" in code
    assert f"from-[{colours['hero'][0]}]" in code


def test_generation_theme_property(themed_generation):
    assert themed_generation.theme == THEME
    themed_generation.metadata = None
    assert themed_generation.theme is None
    themed_generation.metadata = {"theme": "not a dict"}
    assert themed_generation.theme is None


def test_project_detail_rerender_keeps_theme(api_client, themed_generation):
    api_client.force_authenticate(user=themed_generation.project.user)
    response = api_client.get(f"/api/v1/projects/{themed_generation.project.id}/")
    assert response.status_code == 200
    _assert_themed(response.data["latest_generation"]["code"])


def test_cache_patch_rerender_keeps_theme(themed_generation):
    gid = str(themed_generation.id)
    generation_cache.GenerationCache.store_generation(
        gid, BARE_SCHEMA, "old", {"design_plan": {"theme": THEME}})
    patch = [{"op": "replace", "path": "/children/0/children/0/content", "value": "Edited"}]
    assert generation_cache.GenerationCache.apply_patch(gid, patch) is not None
    _assert_themed(generation_cache.GenerationCache.get_generation(gid)["code"])


def test_version_views_rerender_keeps_theme(api_client, themed_generation):
    from patching.models import Patch
    api_client.force_authenticate(user=themed_generation.project.user)
    patch = Patch.objects.create(
        generation=themed_generation, user=themed_generation.project.user,
        patch_data=[{"op": "replace", "path": "/children/0/children/0/content", "value": "v2"}], description="")
    response = api_client.get(f"/api/v1/patching/{themed_generation.id}/version/{patch.id}/")
    assert response.status_code == 200, response.data
    _assert_themed(response.data["code"])


# ---------------------------------------------------------------------------
# Parser-level proof (needs node + the frontend's node_modules, like test_codegen_safety)
# ---------------------------------------------------------------------------

import os
import shutil
import subprocess

FRONTEND_MODULES = Path(os.environ.get("TSX_CHECK_NODE_MODULES", Path(__file__).resolve().parents[3] / "dburst-frontend" / "node_modules"))
needs_node = pytest.mark.skipif(
    not shutil.which("node") or not (FRONTEND_MODULES / "typescript" / "package.json").exists(),
    reason="needs node + dburst-frontend/node_modules",
)

CLASSNAME_PROBE = r"""
const ts = require(process.argv[1]);
let src = ""; process.stdin.on("data", d => src += d).on("end", () => {
  const sf = ts.createSourceFile("g.tsx", src, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const out = [];
  (function walk(n) {
    if (ts.isJsxAttribute(n) && n.name.getText(sf) === "className") {
      const i = n.initializer;
      out.push(i && ts.isStringLiteral(i) ? i.text : i && i.expression && ts.isStringLiteral(i.expression) ? i.expression.text : null);
    }
    ts.forEachChild(n, walk);
  })(sf);
  console.log(JSON.stringify({ errors: sf.parseDiagnostics.length, classNames: out }));
});
"""

SCAN_PROBE = r"""
const { Scanner } = require(process.argv[1]);
const fs = require("fs"), path = require("path"), os = require("os");
const dir = fs.mkdtempSync(path.join(os.tmpdir(), "dburst-scan-"));
fs.writeFileSync(path.join(dir, "App.tsx"), fs.readFileSync(0, "utf8"));
const scanner = new Scanner({ sources: [{ base: dir, pattern: "**/*.tsx", negated: false }] });
console.log(JSON.stringify(scanner.scan()));
fs.rmSync(dir, { recursive: true });
"""


def _corpus_source():
    schema = {"type": "Root", "children": [node("Div", c) for c in CORPUS]}
    return ReactCodeGenerator(SchemaValidator.validate(schema)).generate()


@needs_node
def test_typescript_parser_decodes_every_corpus_classname_to_the_original_string():
    out = subprocess.run(["node", "-e", CLASSNAME_PROBE, str(FRONTEND_MODULES / "typescript")],
                         input=_corpus_source(), capture_output=True, text=True, timeout=120, check=True)
    report = json.loads(out.stdout)
    assert report["errors"] == 0
    # The Root's own className (the viewport-height default), then one per corpus entry, in order.
    assert report["classNames"] == ["min-h-screen"] + [normalised(c) for c in CORPUS]


@needs_node
@pytest.mark.skipif(not (FRONTEND_MODULES / "@tailwindcss" / "oxide").exists(), reason="needs @tailwindcss/oxide")
def test_tailwind_scanner_finds_every_class_in_the_generated_source():
    """Tailwind builds only what its scanner finds in the source text. Classes
    must therefore appear verbatim, which is why a `"` goes in a single-quoted
    JSX string, not an escaped JS one. (Values that still need a JSON literal --
    backslashes, entities, both quote kinds -- are the documented exceptions.)"""
    code = _corpus_source()
    out = subprocess.run(["node", "-e", SCAN_PROBE, str(FRONTEND_MODULES / "@tailwindcss" / "oxide")],
                         input=code, capture_output=True, text=True, timeout=120, check=True)
    found = set(json.loads(out.stdout))
    needs_json = [c for c in CORPUS if codegen_module._UNSAFE_ATTR.search(normalised(c))
                  and not ('"' in c and "'" not in c and not codegen_module._NEEDS_JSON.search(c))]
    assert len(needs_json) < 12  # the exceptions stay rare
    missing = sorted({t for c in CORPUS if c not in needs_json for t in normalised(c).split()} - found)
    # Not classes Tailwind could ever have seen anyway.
    assert [t for t in missing if not t.startswith(("text-[red", "bg-#", "_"))] == []
