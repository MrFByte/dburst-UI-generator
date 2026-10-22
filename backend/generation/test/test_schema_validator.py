import pytest
from generation.schema_validator import (
    ALLOWED_COMPONENT_TYPES,
    FIXED_IMAGE,
    MAX_CLASSNAME_LENGTH,
    MAX_SCHEMA_DEPTH,
    MAX_SCHEMA_NODES,
    SchemaValidator,
)


# ------------------------------
# VALIDATION: TYPE + STRUCTURE
# ------------------------------

def test_schema_requires_dict():
    """Schema must be a dictionary."""
    with pytest.raises(ValueError, match="Schema must be a dictionary"):
        SchemaValidator.validate(["not", "a", "dict"])


def test_schema_requires_type_field():
    """Schema must contain a 'type' field."""
    with pytest.raises(ValueError, match="Schema must have 'type' field"):
        SchemaValidator.validate({})


def test_schema_allows_unknown_component_type():
    """Unknown component types should be allowed (with warning)."""
    schema = {"type": "UnknownComponent"}
    # Should not raise
    validated = SchemaValidator.validate(schema)
    assert validated["type"] == "UnknownComponent"


def test_schema_accepts_valid_component_type():
    """Valid types should pass successfully."""
    for comp in ALLOWED_COMPONENT_TYPES:
        schema = {"type": comp}
        validated = SchemaValidator.validate(schema)
        assert validated["type"] == comp


# ------------------------------
# CLASSNAME: passed through (no whitelist)
# ------------------------------

@pytest.mark.parametrize("classes", [
    "-translate-x-1/2 -mt-4 -z-10",
    "dark:bg-black first:pt-0 last:pb-0 odd:bg-gray-50 placeholder:text-gray-400",
    "before:content-[''] after:absolute",
    "group group-hover:text-white peer peer-checked:bg-blue-500",
    "container grow shrink-0 order-2 size-4 outline-none blur-sm filter",
    "[&>*]:p-2 [&_svg]:size-4",
    "!font-bold !mt-0",
    "sm:p-6 hover:bg-blue-500 md:text-xl lg:grid-cols-[1fr_2fr] bg-[#1a1a2e]",
    "@container @lg:flex",
])
def test_valid_tailwind_classes_preserved(classes):
    schema = {"type": "Section", "props": {"className": classes}}
    assert SchemaValidator.validate(schema)["props"]["className"] == classes


def test_classname_whitespace_collapsed_and_control_chars_dropped():
    schema = {"type": "Card", "props": {"className": "  p-4\n\t text-lg\x00 \x1b[31m  "}}
    assert SchemaValidator.validate(schema)["props"]["className"] == "p-4 text-lg [31m"


@pytest.mark.parametrize("value", [None, 42, ["p-4", 7], {"a": 1}])
def test_classname_non_string_becomes_empty(value):
    schema = {"type": "Card", "props": {"className": value}}
    assert SchemaValidator.validate(schema)["props"]["className"] == ""


def test_classname_list_of_strings_is_joined_not_dropped():
    """A model that emits ["p-4", "bg-red-500"] meant those classes."""
    schema = {"type": "Card", "props": {"className": ["p-4", "bg-red-500", "hover:bg-[#abc]"]}}
    assert SchemaValidator.validate(schema)["props"]["className"] == "p-4 bg-red-500 hover:bg-[#abc]"


def test_classname_capped_at_class_boundary():
    schema = {"type": "Card", "props": {"className": " ".join(["px-4"] * 1000)}}
    cleaned = SchemaValidator.validate(schema)["props"]["className"]
    assert len(cleaned) <= MAX_CLASSNAME_LENGTH
    assert set(cleaned.split(" ")) == {"px-4"}


def test_classname_is_not_responsible_for_escaping():
    """Quotes/braces stay in the schema; codegen escapes them (see test_codegen_safety)."""
    schema = {"type": "Card", "props": {"className": 'p-1"onClick={alert(1)}'}}
    assert SchemaValidator.validate(schema)["props"]["className"] == 'p-1"onClick={alert(1)}'


def test_classname_empty_string_safe():
    schema = {"type": "Card", "props": {"className": ""}}
    validated = SchemaValidator.validate(schema)
    assert validated["props"]["className"] == ""


def test_classname_absent_safe():
    schema = {"type": "Text", "props": {}}
    validated = SchemaValidator.validate(schema)
    assert "className" not in validated["props"]


# ------------------------------
# PROPS
# ------------------------------

def test_unknown_props_are_kept():
    schema = {"type": "Button", "props": {"variant": "outline", "size": "lg", "data-x": 1}}
    props = SchemaValidator.validate(schema)["props"]
    assert props == {"variant": "outline", "size": "lg", "data-x": 1}


def test_invalid_id_and_tag_dropped_booleans_coerced():
    schema = {"type": "Text", "props": {"id": "bad id!", "tag": "script", "disabled": 1}}
    props = SchemaValidator.validate(schema)["props"]
    assert "id" not in props and "tag" not in props
    assert props["disabled"] is True


# ------------------------------
# STRUCTURE
# ------------------------------

def test_props_must_be_dict():
    with pytest.raises(ValueError, match="Props must be a dictionary"):
        SchemaValidator.validate({"type": "Card", "props": ["x"]})


def test_children_must_be_list():
    with pytest.raises(ValueError, match="Children must be a list"):
        SchemaValidator.validate({"type": "Card", "children": "text"})


def test_type_must_be_string():
    with pytest.raises(ValueError, match="type"):
        SchemaValidator.validate({"type": ["Card"]})


def test_content_only_node_repaired_to_text_and_content_coerced():
    validated = SchemaValidator.validate({"content": 42})
    assert validated["type"] == "Text"
    assert validated["content"] == "42"


def test_child_errors_raise():
    with pytest.raises(ValueError):
        SchemaValidator.validate({"type": "Root", "children": [{"type": "Card", "props": "x"}]})


def _nested(depth):
    node = {"type": "div"}
    for _ in range(depth - 1):
        node = {"type": "div", "children": [node]}
    return node


def test_depth_limit():
    SchemaValidator.validate(_nested(MAX_SCHEMA_DEPTH))
    with pytest.raises(ValueError, match="depth"):
        SchemaValidator.validate(_nested(MAX_SCHEMA_DEPTH + 1))


def test_node_count_limit():
    ok = {"type": "Root", "children": [{"type": "div"}] * (MAX_SCHEMA_NODES - 1)}
    SchemaValidator.validate(ok)
    too_many = {"type": "Root", "children": [{"type": "div"} for _ in range(MAX_SCHEMA_NODES)]}
    with pytest.raises(ValueError, match="nodes"):
        SchemaValidator.validate(too_many)


def test_string_children_count_toward_node_limit():
    schema = {"type": "Root", "children": ["x"] * MAX_SCHEMA_NODES}
    with pytest.raises(ValueError, match="nodes"):
        SchemaValidator.validate(schema)


def test_enforce_fixed_image_is_static():
    schema = {"type": "Root", "children": [
        {"type": "Image", "props": {"src": ""}},
        {"type": "Image", "props": {"src": "https://via.placeholder.com/1"}},
        {"type": "Image", "props": {"src": "https://cdn.real.com/a.png"}},
    ]}
    SchemaValidator.enforce_fixed_image(schema)
    srcs = [c["props"]["src"] for c in schema["children"]]
    assert srcs == [FIXED_IMAGE, FIXED_IMAGE, "https://cdn.real.com/a.png"]


# ------------------------------
# CHILD VALIDATION (RECURSIVE)
# ------------------------------

def test_recursive_validation_of_children():
    schema = {
        "type": "Root",
        "props": {"className": "p-4  shadow-lg"},
        "children": [
            {"type": "Text", "props": {"className": "text-2xl dark:text-white"}, "content": "Hello world"},
            {"type": "Section", "props": {}, "children": [
                {"type": "Button", "props": {"className": "bg-blue-500 hover:bg-blue-700 !px-2"}},
                "plain text",
            ]},
        ],
    }

    validated = SchemaValidator.validate(schema)

    assert validated["props"]["className"] == "p-4 shadow-lg"
    assert validated["children"][0]["props"]["className"] == "text-2xl dark:text-white"
    assert validated["children"][1]["children"][0]["props"]["className"] == "bg-blue-500 hover:bg-blue-700 !px-2"
    assert validated["children"][1]["children"][1] == "plain text"


def test_recursive_child_invalid_type_allowed():
    """If a child contains an invalid type, allow it."""
    schema = {
        "type": "Root",
        "children": [
            {"type": "Section"},
            {"type": "INVALID_CHILD"}
        ],
    }

    # Should not raise
    validated = SchemaValidator.validate(schema)
    assert validated["children"][1]["type"] == "INVALID_CHILD"
