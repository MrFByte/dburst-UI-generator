"""
Codegen output safety: whatever strings a schema carries, the generated TSX
can't gain new attributes, expressions, tags, imports or dangerous URLs.
"""
import copy
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from generation.codegen import ReactCodeGenerator, jsx_attr, jsx_text, render_schema, safe_url
from generation.schema_validator import FIXED_IMAGE, SchemaValidator

HOSTILE = 'x" onClick={() => alert(1)} data-a="{y}</div><script>alert(2)</script>&quot;\\\n'


def gen(schema):
    return ReactCodeGenerator(copy.deepcopy(schema)).generate()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def test_jsx_attr_benign_unchanged():
    assert jsx_attr("className", "p-4 [&>*]:p-2 !font-bold -mt-4") == ' className="p-4 [&>*]:p-2 !font-bold -mt-4"'


@pytest.mark.parametrize("value", ["a\\b", "a\nb", "&quot;", "&#34;", "\u2028", "a'b\"c", 'a"b\\c', 'a"b&amp;'])
def test_jsx_attr_uses_json_literal_when_needed(value):
    out = jsx_attr("alt", value)
    assert out.startswith(" alt={") and out.endswith("}")
    assert json.loads(out[len(" alt={"):-1]) == value


@pytest.mark.parametrize("value", ['a"b', 'font-["Playfair_Display"]', 'bg-[url("/x.png")]', 'x"onClick={alert(1)}'])
def test_jsx_attr_keeps_a_double_quote_verbatim_in_single_quotes(value):
    """JSX strings have no escapes, so the value stays readable as-is (Tailwind's
    scanner extracts classes from the source text); `{` and `"` inside are inert."""
    assert jsx_attr("className", value) == f" className='{value}'"


def test_jsx_text_escapes_specials():
    assert jsx_text("a{b}<c>&d") == "a&#123;b&#125;&lt;c&gt;&amp;d"
    assert jsx_text("Plain text, it's \"fine\"") == "Plain text, it's \"fine\""


@pytest.mark.parametrize("url", [
    "https://example.com/a?b=1#c", "http://example.com", "mailto:a@b.co", "tel:+123",
    "#section", "/pricing", "./a.png", "../up.png", "HTTPS://EXAMPLE.COM",
])
def test_safe_url_allows(url):
    assert safe_url(url, "#") == url


@pytest.mark.parametrize("url", [
    "javascript:alert(1)", "JavaScript:alert(1)", "  javascript:alert(1)", "\x00javascript:alert(1)",
    "java\tscript:alert(1)", "java\nscript:alert(1)", "data:text/html,<script>", "vbscript:x",
    "file:///etc/passwd", "//evil.com/a", "/\\evil.com", "evil.com", "about:blank", None, 123,
])
def test_safe_url_blocks(url):
    assert safe_url(url, "#") == "#"


def test_safe_url_strips_leading_whitespace():
    assert safe_url("  https://a.com", "#") == "https://a.com"


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def test_hostile_classname_cannot_add_attributes():
    out = gen({"type": "div", "props": {"className": 'p-1"onClick={alert(1)}'}})
    assert """<div className='p-1"onClick={alert(1)}' />""" in out
    assert 'className="p-1"onClick' not in out


@pytest.mark.parametrize("node_type", ["Text", "Button", "Link", "Section", "Card", "Badge"])
def test_content_braces_and_tags_escaped(node_type):
    out = gen({"type": node_type, "content": "{alert(1)}<img src=x onerror=alert(2)>"})
    assert "&#123;alert(1)&#125;&lt;img src=x onerror=alert(2)&gt;" in out
    assert "{alert(1)}" not in out and "<img src=x" not in out


def test_string_children_escaped():
    out = gen({"type": "Flex", "children": ["{boom}", {"type": "Text", "children": ["<b>hi</b>", {"type": "Text", "content": "}"}]}]})
    assert "&#123;boom&#125;" in out
    assert "&lt;b&gt;hi&lt;/b&gt;" in out
    assert "&#125;" in out


def test_alt_placeholder_id_type_escaped():
    out = gen({"type": "Root", "children": [
        {"type": "Image", "props": {"src": "https://a.com/x.png", "alt": 'a"b{c}'}},
        {"type": "Input", "props": {"placeholder": 'p"q', "type": 'text" autoFocus x="'}},
        {"type": "div", "props": {"id": 'i"d'}},
    ]})
    assert """alt='a"b{c}'""" in out
    assert """placeholder='p"q'""" in out
    assert """type='text" autoFocus x="'""" in out
    assert """id='i"d'""" in out


@pytest.mark.parametrize("node_type", ["Hero", "Timeline", "TimelineItem"])
def test_special_layouts_escape_classname(node_type):
    out = gen({"type": node_type, "props": {"className": 'bg-x"onClick={x}'}, "children": []})
    assert """className='bg-x"onClick={x}""" in out  # still inside one single-quoted string


def test_href_neutralized_and_allowed():
    out = gen({"type": "Root", "children": [
        {"type": "Link", "props": {"href": "javascript:alert(1)"}, "content": "bad"},
        {"type": "Link", "props": {"href": "data:text/html,x"}, "content": "bad2"},
        {"type": "Link", "props": {"href": "https://ok.com"}, "content": "ok"},
        {"type": "Link", "props": {"href": "mailto:a@b.co"}, "content": "mail"},
        {"type": "Link", "props": {"href": "/relative"}, "content": "rel"},
    ]})
    assert "javascript:" not in out and "data:" not in out
    assert '<a href="#">bad</a>' in out and '<a href="#">bad2</a>' in out
    assert 'href="https://ok.com"' in out and 'href="mailto:a@b.co"' in out and 'href="/relative"' in out


def test_src_neutralized_and_allowed():
    out = gen({"type": "Root", "children": [
        {"type": "Image", "props": {"src": "javascript:alert(1)", "alt": "a"}},
        {"type": "Image", "props": {"src": "data:image/svg+xml,<svg onload=alert(1)>", "alt": "b"}},
        {"type": "Image", "props": {"src": "https://cdn.ok.com/a.png", "alt": "c"}},
    ]})
    assert "javascript:" not in out and "data:" not in out
    assert out.count(f'src="{FIXED_IMAGE}"') == 2
    assert 'src="https://cdn.ok.com/a.png"' in out


def test_bad_icon_names_skipped():
    schema = {"type": "Root", "children": [
        {"type": "Icon", "props": {"name": "Mail"}},
        {"type": "Icon", "props": {"name": "Mail } from 'x'; alert(1); import {"}},
        {"type": "Icon", "props": {"name": "React"}},
        {"type": "Icon", "props": {"name": "Button"}},
        {"type": "Badge", "props": {"icon": "bad-name"}, "metadata": {"icon": "1Bad"}},
    ]}
    gen_ = ReactCodeGenerator(copy.deepcopy(schema))
    out = gen_.generate()
    assert gen_.used_icons == {"Mail"}
    assert "import { Mail } from 'lucide-react';" in out
    assert "alert(1)" not in out
    assert out.count('<span aria-hidden="true" />') == 3


def test_unsafe_types_and_tags_render_as_div():
    out = gen({"type": "Root", "children": [
        {"type": "script", "content": "alert(1)"},
        {"type": "iframe"},
        {"type": "div onClick={x}", "content": "a"},
        {"type": "Text", "props": {"tag": "script"}, "content": "b"},
        {"type": "Text", "children": [{"type": "Text", "props": {"tag": "style"}, "content": "c"}]},
        {"type": "MyWidget", "content": "d"},
    ]})
    assert "<script" not in out and "<iframe" not in out and "<style" not in out and "onClick" not in out
    assert "<div>alert(1)</div>" in out and "<p>b</p>" in out and "<span>c</span>" in out
    assert "<MyWidget>d</MyWidget>" in out  # capitalized identifiers stay components


def test_component_name_must_be_identifier():
    out = ReactCodeGenerator({"type": "div"}, component_name="X() {}; alert(1); function Y").generate()
    assert "export default function GeneratedUI()" in out


def test_malformed_structure_does_not_crash():
    out = gen({"type": ["div"], "props": "nope", "children": "nope", "content": {"a": 1}})
    assert "export default function" in out


def test_render_schema_validates_copy():
    schema = {"type": "Root", "children": [{"type": "Section", "props": "bad"}]}
    with pytest.raises(ValueError):
        render_schema(schema)
    good = {"type": "Paragraph", "content": "x"}
    assert "<p>x</p>" in render_schema(good)
    assert good["type"] == "Paragraph"  # caller's schema untouched


# --------------------------------------------------------------------------
# The hostile schema still produces syntactically valid TSX
# --------------------------------------------------------------------------

def hostile_schema():
    return {"type": "Root", "props": {"className": HOSTILE, "id": HOSTILE}, "children": [
        {"type": "Hero", "props": {"className": HOSTILE}, "children": [
            {"type": "Text", "props": {"tag": "h1", "className": HOSTILE}, "children": [HOSTILE, {"type": "Text", "content": HOSTILE}, {"type": "Badge", "content": HOSTILE}]},
            {"type": "Button", "props": {"className": HOSTILE}, "content": HOSTILE},
            {"type": "Button", "children": [HOSTILE, {"type": "Icon", "props": {"name": HOSTILE}}]},
        ]},
        {"type": "Timeline", "props": {"className": HOSTILE}, "children": [{"type": "TimelineItem", "props": {"className": HOSTILE}, "children": [HOSTILE]}]},
        {"type": "Link", "props": {"href": "javascript:" + HOSTILE, "className": HOSTILE}, "content": HOSTILE},
        {"type": "Image", "props": {"src": HOSTILE, "alt": HOSTILE, "className": HOSTILE}},
        {"type": "Input", "props": {"placeholder": HOSTILE, "type": HOSTILE}},
        {"type": HOSTILE, "content": HOSTILE},
        {"type": "Card", "props": {"className": HOSTILE}, "children": [{"type": "CardTitle", "content": HOSTILE}]},
        {"type": "Grid", "content": HOSTILE},
    ]}


TYPESCRIPT = Path(os.environ.get(
    "TSX_CHECK_TYPESCRIPT",
    Path(__file__).resolve().parents[3] / "dburst-frontend" / "node_modules" / "typescript",
))

# Parses TSX from stdin; prints syntax errors, every JSX attribute name, and the
# kinds of every JSX {expression} found.
TSX_PROBE = r"""
const ts = require(process.argv[1]);
let src = ""; process.stdin.on("data", d => src += d).on("end", () => {
  const sf = ts.createSourceFile("g.tsx", src, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const attrs = new Set(), exprs = new Set(), tags = new Set();
  (function walk(n) {
    if (ts.isJsxAttribute(n)) attrs.add(n.name.getText(sf));
    if (ts.isJsxExpression(n) && n.expression) exprs.add(ts.SyntaxKind[n.expression.kind]);
    if (ts.isJsxOpeningElement(n) || ts.isJsxSelfClosingElement(n)) tags.add(n.tagName.getText(sf));
    ts.forEachChild(n, walk);
  })(sf);
  console.log(JSON.stringify({
    errors: sf.parseDiagnostics.map(d => ts.flattenDiagnosticMessageText(d.messageText, " ")),
    attrs: [...attrs], exprs: [...exprs], tags: [...tags],
    statements: sf.statements.length,
  }));
});
"""


@pytest.mark.skipif(
    not shutil.which("node") or not (TYPESCRIPT / "package.json").exists(),
    reason="needs node + dburst-frontend/node_modules/typescript",
)
def test_hostile_schema_generates_valid_tsx():
    code = gen(hostile_schema())
    result = subprocess.run(
        ["node", "-e", TSX_PROBE, str(TYPESCRIPT)],
        input=code, capture_output=True, text=True, timeout=60, check=True,
    )
    report = json.loads(result.stdout)
    assert report["errors"] == [], code
    # import React, import {...ui}, export default function — nothing injected.
    assert report["statements"] == 3, code
    assert set(report["attrs"]) <= {"className", "id", "src", "alt", "crossOrigin", "href", "placeholder", "type", "aria-hidden"}
    # Every {expression} is a plain string literal.
    assert set(report["exprs"]) <= {"StringLiteral"}
    assert set(report["tags"]) <= {"main", "div", "p", "h1", "span", "Button", "a", "img", "Input", "Card", "CardTitle", "Badge"}


@pytest.mark.skipif(
    not shutil.which("node") or not (TYPESCRIPT / "package.json").exists(),
    reason="needs node + dburst-frontend/node_modules/typescript",
)
def test_validated_hostile_schema_generates_valid_tsx():
    code = ReactCodeGenerator(SchemaValidator.validate(hostile_schema())).generate()
    result = subprocess.run(
        ["node", "-e", TSX_PROBE, str(TYPESCRIPT)],
        input=code, capture_output=True, text=True, timeout=60, check=True,
    )
    assert json.loads(result.stdout)["errors"] == [], code
