import copy
import json
import logging
import re
from typing import Dict, Any, List, Set

from .schema_validator import FIXED_IMAGE

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output safety. Schemas come from an LLM (and from user-supplied patches), and
# every string below is interpolated into TSX source that runs in the preview.
# These helpers guarantee a string can only ever be a string: never JSX,
# never a JS expression, never an attribute break-out, never a dangerous URL.
# They return benign values unchanged, so normal output is byte-identical.
# ---------------------------------------------------------------------------

# What can't appear raw inside a JSX "..." attribute without changing its
# meaning: the quote ends it, an HTML entity (&quot;) is decoded, and
# backslashes/control characters make the source fragile. A lone "&" (as in
# Tailwind's [&>*]:p-2) is literal and stays as-is.
_UNSAFE_ATTR = re.compile(r'["\\\x00-\x1f\x7f\u2028\u2029]|&#?[A-Za-z0-9]+;')
# Still needs a JSON literal even inside single quotes: backslashes, control
# characters, line/paragraph separators and HTML entities.
_NEEDS_JSON = re.compile(r'[\\\x00-\x1f\x7f\u2028\u2029]|&#?[A-Za-z0-9]+;')
_JSX_TEXT_ESCAPES = {"{": "&#123;", "}": "&#125;", "<": "&lt;", ">": "&gt;", "&": "&amp;"}
_JSX_TEXT_SPECIAL = re.compile(r"[{}<>&]")

IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
SAFE_URL_SCHEMES = {"http", "https", "mailto", "tel"}
_URL_SCHEME = re.compile(r"^([a-z][a-z0-9+.\-]*):")

# Lowercase JSX names are real DOM elements; only these may be emitted from a
# schema type. (No script/iframe/object/embed/style/link/meta/base.)
INTRINSIC_TAGS = {
    "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6", "a", "img",
    "ul", "ol", "li", "section", "article", "nav", "header", "footer", "main",
    "aside", "table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption",
    "form", "label", "button", "input", "textarea", "select", "option",
    "strong", "em", "b", "i", "u", "small", "mark", "code", "pre",
    "blockquote", "hr", "br", "figure", "figcaption", "dl", "dt", "dd",
}
TEXT_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "span", "div", "ul", "ol", "li"}

# ---------------------------------------------------------------------------
# Class inspection (read-only). Theme defaults are only added when the schema
# has no colour of its own, so "does it already have a background?" has to
# look at real, unprefixed utilities: `hover:bg-x` or `bg-clip-text` are not
# a page background. Nothing here ever rewrites a class.
# ---------------------------------------------------------------------------
_BG_NON_COLOUR = re.compile(
    r"^bg-(?:clip|origin|blend|repeat|no-repeat|cover|contain|auto|center|top|bottom|left|right|"
    r"fixed|local|scroll|none|\[(?:length|position|size|percentage):)"
)
_TEXT_COLOUR = re.compile(
    r"^text-(?:white|black|transparent|current|inherit|[a-z]+-\d{2,3}(?:/\d+)?|"
    r"\[(?:#|rgb|hsl|oklch|color:)[^\]]*\](?:/\d+)?)$"
)
_BRACKETS = re.compile(r"\[[^\]]*\]")


def _utilities(class_name: str):
    """Base-state utilities: no `hover:`/`md:`/`[&>*]:` variant, and without
    the v3 `!` prefix or v4 `!` suffix."""
    for token in class_name.split():
        if token.startswith("[") or ":" in _BRACKETS.sub("", token):
            continue
        yield token.strip("!")


def has_background(class_name: str) -> bool:
    """A base-state background colour or gradient (bg-red-500, bg-[#abc],
    bg-gradient-to-r, bg-linear-to-r...); not bg-clip-text, not a variant."""
    return any(u.startswith("bg-") and not _BG_NON_COLOUR.match(u) for u in _utilities(class_name))


def has_text_colour(class_name: str) -> bool:
    return any(_TEXT_COLOUR.match(u) for u in _utilities(class_name))


def has_utility(class_name: str, prefix: str) -> bool:
    return any(u.startswith(prefix) for u in _utilities(class_name))


def jsx_attr(name: str, value: Any) -> str:
    """` name="value"`; ` name='value'` for a value with a double quote but no
    single quote (JSX strings have no escapes, so the class stays verbatim in
    the source, which is what Tailwind's scanner reads: font-["Playfair_Display"]);
    else ` name={"value"}` (a JSON string literal, a valid JS string) when the
    value contains anything else that could break out."""
    value = "" if value is None else str(value)
    if _UNSAFE_ATTR.search(value):
        if '"' in value and "'" not in value and not _NEEDS_JSON.search(value):
            return f" {name}='{value}'"
        return f" {name}={{{json.dumps(value)}}}"
    return f' {name}="{value}"'


def jsx_text(value: Any) -> str:
    """Text between JSX tags: { } < > & become HTML entities, so the text can
    never open an expression or a tag (React renders the same characters)."""
    value = "" if value is None else str(value)
    return _JSX_TEXT_SPECIAL.sub(lambda m: _JSX_TEXT_ESCAPES[m.group()], value)


def safe_url(value: Any, fallback: str) -> str:
    """Allows http(s), mailto, tel, #anchors and relative paths (/x, ./x, ../x).
    Anything else (javascript:, data:, vbscript:, file:, //host, bare words)
    becomes `fallback`."""
    if not isinstance(value, str):
        return fallback
    url = value.lstrip("\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f"
                       "\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f ")
    if not url:
        return fallback
    # Browsers drop tab/CR/LF anywhere in a URL ("java\tscript:"), so check
    # the scheme on that form.
    probe = re.sub(r"[\t\r\n]", "", url).lower()
    if probe.startswith("#"):
        return url
    if probe.startswith("/"):
        # "//host" and "/\\host" are protocol-relative to browsers.
        return fallback if probe[1:2] in ("/", "\\") else url
    if probe.startswith("./") or probe.startswith("../"):
        return url
    match = _URL_SCHEME.match(probe)
    if match and match.group(1) in SAFE_URL_SCHEMES:
        return url
    return fallback


def is_identifier(name: Any) -> bool:
    return isinstance(name, str) and bool(IDENTIFIER.match(name))


def render_schema(schema: Dict[str, Any], component_name: str = "GeneratedUI", theme: Any = None) -> str:
    """Validate (a copy of) `schema` and generate its code — for paths that
    regenerate from stored or patched schemas. Raises ValueError if invalid."""
    from .schema_validator import SchemaValidator

    validated = SchemaValidator.validate(copy.deepcopy(schema))
    return ReactCodeGenerator(validated, component_name, theme=theme).generate()

def apply_theme_defaults(schema: Dict[str, Any], theme: Any) -> Dict[str, Any]:
    """Write the theme's defaults (page background, hero gradient, card surface,
    timeline accents) into the schema's own classNames, in place.

    Generated code gets these defaults at codegen time, but every other view of
    the schema (edit mode's renderer, a re-render without the theme, version
    history) would not. Baking them in makes the stored schema the one source
    of truth. Additive only, and idempotent: see ReactCodeGenerator.with_defaults.
    """
    generator = ReactCodeGenerator({}, theme=theme)

    def walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        node_type = node.get("type")
        props = node.get("props")
        if isinstance(node_type, str) and (props is None or isinstance(props, dict)):
            current = (props or {}).get("className")
            current = current if isinstance(current, str) else ""
            updated = generator.with_defaults(node_type, current)
            new_props = {**(props or {})}
            if updated != current:
                new_props["className"] = updated
            if node_type == "TimelineItem" and "dotClassName" not in new_props and generator.colors.get("accent"):
                # The dot drawn beside the item takes the theme accent too.
                new_props["dotClassName"] = f"bg-[{generator.colors['accent']}]"
            if new_props != (props or {}):
                node["props"] = new_props
        for child in node.get("children") or []:
            walk(child)

    walk(schema)
    return schema


class ReactCodeGenerator:
    """Generate modern React code from schema with proper nesting support"""
    
    COMPONENT_IMPORTS = {
        "Button": "shadcn/ui",
        "Input": "shadcn/ui",
        "Label": "shadcn/ui",  # <--- Added
        "Select": "shadcn/ui",
        "Badge": "shadcn/ui",
        "Card": "shadcn/ui",
        "CardHeader": "shadcn/ui",
        "CardContent": "shadcn/ui",
        "CardFooter": "shadcn/ui",
        "CardTitle": "shadcn/ui",
        "CardDescription": "shadcn/ui",
        "Separator": "shadcn/ui",
        "Table": "shadcn/ui",
        "TableHeader": "shadcn/ui",
        "TableBody": "shadcn/ui",
        "TableRow": "shadcn/ui",
        "TableCell": "shadcn/ui",
        "TableHead": "shadcn/ui",
    }
    
    def __init__(self, schema: Dict[str, Any], component_name: str = "GeneratedUI", theme: Any = None):
        self.schema = schema if isinstance(schema, dict) else {}
        self.component_name = component_name if is_identifier(component_name) else "GeneratedUI"
        self.colors = self._theme_colors(theme)
        self.used_components = set()
        self.used_icons = set()
        self.indent_size = 2
    
    def generate(self) -> str:
        """Generate complete React component"""
        self._scan_for_imports(self.schema)
        
        imports = self._generate_imports()
        component_body = self._render_component(self.schema, indent=1)
        
        return f"""{imports}

export default function {self.component_name}() {{
  return (
{component_body}
  );
}}
"""
    
    def _scan_for_imports(self, node: Dict[str, Any]):
        """Recursively scan for required imports"""
        node_type = node.get("type")
        if not isinstance(node_type, str):
            node_type = None
        props = self._props(node)
        
        # 1. Scan for Shadcn Components
        if node_type in self.COMPONENT_IMPORTS:
            self.used_components.add(node_type)
        
        # 2. Scan for Icons (NEW LOGIC)
        # Case A: {"type": "Icon", "props": {"name": "Mail"}}
        if node_type == "Icon":
            icon_name = props.get("name")
            if icon_name:
                self._add_icon(icon_name)
        
        metadata = node.get("metadata")
        metadata_icon = metadata.get("icon") if isinstance(metadata, dict) else None
        if metadata_icon:
            self._add_icon(metadata_icon)
        
        if "icon" in props:
            self._add_icon(props["icon"])
        
        children = self._children(node)
        for child in children:
            if isinstance(child, dict):
                self._scan_for_imports(child)
    
    def _add_icon(self, name: Any):
        """Icon names go into an import and a JSX tag, so only plain
        identifiers that don't collide with our other bindings."""
        if not self._is_safe_icon(name):
            logger.warning(f"Skipping invalid icon name: {name!r}")
            return
        self.used_icons.add(name)

    def _is_safe_icon(self, name: Any) -> bool:
        reserved = set(self.COMPONENT_IMPORTS) | {"React", self.component_name}
        return is_identifier(name) and name not in reserved

    @staticmethod
    def _props(node: Dict[str, Any]) -> Dict[str, Any]:
        props = node.get("props")
        return props if isinstance(props, dict) else {}

    @staticmethod
    def _children(node: Dict[str, Any]) -> List:
        children = node.get("children")
        return children if isinstance(children, list) else []

    @staticmethod
    def _str(value: Any) -> str:
        return value if isinstance(value, str) else ("" if value is None else str(value))

    def _generate_imports(self) -> str:
        """Generate import statements"""
        imports = ["import React from 'react';"]
        
        if self.used_components:
            components = sorted(list(self.used_components))
            imports.append(f"import {{ {', '.join(components)} }} from '@/components/ui';")
        
        if self.used_icons:
            icons = sorted(list(self.used_icons))
            imports.append(f"import {{ {', '.join(icons)} }} from 'lucide-react';")
        
        return "\n".join(imports)
    
    @staticmethod
    def _theme_colors(theme: Any) -> Dict[str, Any]:
        """Valid hex colours from a design_plan theme or its color_scheme.
        Anything that isn't a plain #hex is dropped, so these are safe to put
        in arbitrary-value classes."""
        if isinstance(theme, dict) and isinstance(theme.get("color_scheme"), dict):
            theme = theme["color_scheme"]
        if not isinstance(theme, dict):
            return {}
        colors = {
            key: theme[key]
            for key in ("background", "surface", "primary", "secondary", "accent", "on_hero", "text")
            if isinstance(theme.get(key), str) and HEX_COLOR.match(theme[key])
        }
        hero = theme.get("hero")
        if isinstance(hero, (list, tuple)) and len(hero) == 2 and all(isinstance(h, str) and HEX_COLOR.match(h) for h in hero):
            colors["hero"] = tuple(hero)
        return colors

    def _default_classes(self) -> Dict[str, str]:
        """Default colour classes for Hero/Timeline when the schema gives none:
        the theme's colours if known, else a clearly coloured gradient."""
        c = self.colors
        hero = c.get("hero") or ((c["primary"], c.get("secondary") or c.get("accent")) if c.get("primary") and (c.get("secondary") or c.get("accent")) else None)
        return {
            "hero": f"bg-gradient-to-br from-[{hero[0]}] to-[{hero[1]}] text-[{c.get('on_hero', '#ffffff')}]" if hero
                    else "bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white",
            "timeline_border": f"border-[{c['primary']}]" if c.get("primary") else "border-indigo-400",
            "timeline_item": f"bg-[{c['surface']}] border-l-4 border-[{c.get('accent') or c.get('primary')}]"
                             if c.get("surface") and (c.get("accent") or c.get("primary"))
                             else "bg-indigo-50 border-l-4 border-pink-500",
            "timeline_dot": f"bg-[{c['accent']}]" if c.get("accent") else "bg-pink-500",
        }

    def with_defaults(self, node_type: str, class_name: str) -> str:
        """`class_name` plus the defaults a node type gets when the schema gives
        it no colour of its own. Purely additive: the classes passed in are
        never removed or edited, and a node that already has a background is
        left alone (so applying this twice changes nothing)."""
        c = self.colors
        defaults = self._default_classes()
        extra = []
        if node_type == "Root":
            # A themed page gets its background (and the text colour that was
            # checked against it); the page always fills the viewport so the
            # background doesn't stop halfway down.
            if c.get("background") and not has_background(class_name):
                extra.append(f"bg-[{c['background']}]")
                if c.get("text") and not has_text_colour(class_name):
                    extra.append(f"text-[{c['text']}]")
            if not has_utility(class_name, "min-h-"):
                extra.append("min-h-screen")
        elif node_type == "Hero":
            # Saturated default (theme colours, else indigo->pink) if it has no background.
            if not has_background(class_name):
                extra.append(f"{defaults['hero']} rounded-2xl shadow-lg p-12")
            elif "rounded" not in class_name:
                extra.append("rounded-2xl shadow-lg p-12")
        elif node_type == "Timeline":
            if "border-l" not in class_name:
                extra.append(f"relative pl-8 border-l-2 {defaults['timeline_border']} space-y-8")
        elif node_type == "TimelineItem":
            if not has_background(class_name):
                extra.append(f"{defaults['timeline_item']} rounded-lg p-6 shadow-md")
        elif node_type == "Card":
            if c.get("surface") and not has_background(class_name):
                extra.append(f"bg-[{c['surface']}]")
        return " ".join([class_name, *extra]).strip() if extra else class_name

    def _render_component(self, node: Dict[str, Any], indent: int = 1) -> str:
        """Recursively render component tree"""
        space = "  " * indent
        node_type = node.get("type", "div")
        if not isinstance(node_type, str):
            node_type = "div"
        props = self._props(node)
        children = self._children(node)
        content = jsx_text(node.get("content", ""))
        
        # Extract props
        className = self._str(props.get("className", ""))
        defaults = self._default_classes()
        className = self.with_defaults(node_type, className)
        id_attr = self._str(props.get("id", ""))
        # Specific props
        src = safe_url(props.get("src", ""), fallback=FIXED_IMAGE)
        alt = self._str(props.get("alt", ""))
        href = safe_url(props.get("href", ""), fallback="#")
        placeholder = self._str(props.get("placeholder", ""))
        type_attr = self._str(props.get("type", "")) # for input type="email"
        
        # Build attribute strings
        class_attr = jsx_attr("className", className) if className else ""
        id_attr_str = jsx_attr("id", id_attr) if id_attr else ""
        
        # Map component types to HTML/React elements
        type_map = {
            "Root": "main",
            "Section": "section",
            "Container": "div",
            "Grid": "div",
            "Flex": "div",
            "Div": "div", # Added explicit Div
            "Hero": "div", # Hero renders as div
            "Timeline": "div", # Timeline renders as div
            "TimelineItem": "div", # TimelineItem renders as div
            "Form": "form",
            "Label": "Label", # Changed to Capital L (Shadcn component)
            "List": "ul",
            "ListItem": "li",
        }
        
        # Default to mapped tag or the type itself — but only if it's a safe
        # JSX name: a known DOM element, or a capitalized identifier (component).
        html_tag = type_map.get(node_type, node_type)
        
        # --- RENDER LOGIC ---

        # 1. Icons (NEW)
        if node_type == "Icon":
            icon_name = props.get("name", "HelpCircle")
            if not self._is_safe_icon(icon_name):
                # Skipped from the imports too; keep the slot so layouts hold.
                return f'{space}<span{class_attr} aria-hidden="true" />'
            return f'{space}<{icon_name}{class_attr} />'

        # 2. Text (Handle mixed content)
        elif node_type == "Text":
            tag = props.get("tag", "p")
            tag = tag if tag in TEXT_TAGS else "p"
            if children:
                children_html = "".join(self._render_inline_component(child, indent) for child in children)
                return f'{space}<{tag}{class_attr}{id_attr_str}>\n{children_html}\n{space}</{tag}>'
            else:
                return f'{space}<{tag}{class_attr}{id_attr_str}>{content}</{tag}>'
        
        # 3. Inputs
        elif node_type == "Input":
            placeholder_attr = jsx_attr("placeholder", placeholder) if placeholder else ""
            type_attr_str = jsx_attr("type", type_attr) if type_attr else ""
            return f'{space}<Input{class_attr}{placeholder_attr}{type_attr_str}{id_attr_str} />'
        
        # 4. Images
        elif node_type == "Image":
            # crossOrigin switches the browser's fetch from opaque no-cors mode
            # (where Cross-Origin-Embedder-Policy only allows a load if the
            # response sets Cross-Origin-Resource-Policy, which our image
            # sources don't) to real CORS mode (where Access-Control-Allow-Origin
            # is what's checked instead, and both Pixabay and placehold.co send
            # "*"). Without this, every image is blocked inside the WebContainer
            # live-preview, which runs under COEP for cross-origin isolation.
            return f'{space}<img{jsx_attr("src", src)}{jsx_attr("alt", alt)} crossOrigin="anonymous"{class_attr}{id_attr_str} />'
        
        # 5. Buttons (Handle explicit content vs children)
        elif node_type == "Button":
            if children:
                children_html = self._render_children(children, indent + 1)
                return f'{space}<Button{class_attr}{id_attr_str}>\n{children_html}\n{space}</Button>'
            return f'{space}<Button{class_attr}{id_attr_str}>{content}</Button>'

        # 6. Links
        elif node_type == "Link" or node_type == "Link/A":
            href_attr = jsx_attr("href", href) if href else ' href="#"'
            if children:
                children_html = self._render_children(children, indent + 1)
                return f'{space}<a{href_attr}{class_attr}{id_attr_str}>\n{children_html}\n{space}</a>'
            return f'{space}<a{href_attr}{class_attr}{id_attr_str}>{content}</a>'

        # 7. Hero, Timeline, TimelineItem (render as divs with special styling)
        elif node_type == "Hero":
            children_html = self._render_children(children, indent + 1)
            return f'{space}<div{class_attr}{id_attr_str}>\n{children_html}\n{space}</div>'
        
        elif node_type == "Timeline":
            children_html = self._render_children(children, indent + 1)
            return f'{space}<div{class_attr}{id_attr_str}>\n{children_html}\n{space}</div>'
        
        elif node_type == "TimelineItem":
            # TimelineItem gets a tinted card with an accent edge and a dot indicator
            children_html = self._render_children(children, indent + 1)
            # Wrap in a container with the dot
            dot_colour = props.get("dotClassName")
            dot_colour = dot_colour if isinstance(dot_colour, str) and dot_colour.strip() else defaults['timeline_dot']
            dot_attr = jsx_attr("className", f"absolute -left-[2.1rem] top-0 w-4 h-4 {dot_colour} rounded-full border-4 border-white shadow-md")
            return f'{space}<div className="relative">\n{space}  <div{dot_attr}></div>\n{space}  <div{class_attr}{id_attr_str}>\n{children_html}\n{space}  </div>\n{space}</div>'
        
        # 8. Generic Container / Shadcn Components
        # If it has children, render them
        elif not is_identifier(html_tag) or (html_tag[0].islower() and html_tag not in INTRINSIC_TAGS):
            logger.warning(f"Unsafe component type {node_type!r}, rendering as div")
            node = {**node, "type": "div"}
            return self._render_component(node, indent)

        elif children:
            children_html = self._render_children(children, indent + 1)
            return f'{space}<{html_tag}{class_attr}{id_attr_str}>\n{children_html}\n{space}</{html_tag}>'
        
        # 8. Leaf node with content
        elif content:
            return f'{space}<{html_tag}{class_attr}{id_attr_str}>{content}</{html_tag}>'
        
        # 9. Self-closing
        else:
            return f'{space}<{html_tag}{class_attr}{id_attr_str} />'

    def _render_inline_component(self, node: Dict[str, Any], parent_indent: int) -> str:
        """Render inline components (like span within h1)"""
        space = "  " * (parent_indent + 1)
        if isinstance(node, str):
            # Bare text inside a Text node's children.
            return f'{space}{jsx_text(node)}\n'
        if not isinstance(node, dict):
            return ""
        node_type = node.get("type", "span")
        if not isinstance(node_type, str):
            node_type = "span"
        props = self._props(node)
        content = jsx_text(node.get("content", ""))
        children = self._children(node)
        
        className = self._str(props.get("className", ""))
        tag = props.get("tag", "span")
        tag = tag if tag in TEXT_TAGS else "span"
        class_attr = jsx_attr("className", className) if className else ""
        
        if node_type == "Text":
            if children:
                children_html = "".join(self._render_inline_component(child, parent_indent) for child in children)
                return f'{space}<{tag}{class_attr}>{children_html}</{tag}>\n'
            return f'{space}<{tag}{class_attr}>{content}</{tag}>\n'
            
        return f'{space}<span{class_attr}>{content}</span>\n'
    
    def _render_children(self, children: List, indent: int) -> str:
        """Render array of children"""
        if not children: return ""
        lines = []
        for child in children:
            if isinstance(child, dict):
                lines.append(self._render_component(child, indent))
            elif isinstance(child, str):
                space = "  " * indent
                lines.append(f"{space}{jsx_text(child)}")
        return "\n".join(lines)