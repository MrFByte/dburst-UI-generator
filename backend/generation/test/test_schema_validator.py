import pytest
from generation.schema_validator import SchemaValidator, ALLOWED_COMPONENT_TYPES


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
# CLASSNAME SANITIZATION
# ------------------------------

def test_classname_sanitization_removes_unsafe_classes():
    schema = {
        "type": "Root",
        "props": {
            "className": "p-4 text-lg bad-class border-red superevil()"
        }
    }

    validated = SchemaValidator.validate(schema)
    assert validated["props"]["className"] == "p-4 text-lg border-red"


def test_classname_allows_responsive_prefixes_and_state_modifiers():
    schema = {
        "type": "Section",
        "props": {
            "className": "sm:p-6 hover:bg-blue-500 md:text-xl evil-class"
        }
    }

    validated = SchemaValidator.validate(schema)

    # The allowed ones should remain
    assert "sm:p-6" in validated["props"]["className"]
    assert "hover:bg-blue-500" in validated["props"]["className"]
    assert "md:text-xl" in validated["props"]["className"]

    # The unsafe one should NOT remain
    assert "evil-class" not in validated["props"]["className"]


def test_classname_empty_string_safe():
    schema = {"type": "Card", "props": {"className": ""}}
    validated = SchemaValidator.validate(schema)
    assert validated["props"]["className"] == ""


def test_classname_absent_safe():
    schema = {"type": "Text", "props": {}}
    validated = SchemaValidator.validate(schema)
    assert "className" not in validated["props"]


# ------------------------------
# CHILD VALIDATION (RECURSIVE)
# ------------------------------

def test_recursive_validation_of_children():
    schema = {
        "type": "Root",
        "props": {"className": "p-4 shadow-lg illegal-class"},
        "children": [
            {
                "type": "Text",
                "props": {"className": "text-2xl superwrong"},
                "content": "Hello world"
            },
            {
                "type": "Section",
                "props": {},
                "children": [
                    {
                        "type": "Button",
                        "props": {"className": "bg-blue-500 scary!! hover:bg-blue-700"},
                    }
                ]
            }
        ]
    }

    validated = SchemaValidator.validate(schema)

    # Root class sanitized
    assert validated["props"]["className"] == "p-4 shadow-lg"

    # Text child sanitized
    assert validated["children"][0]["props"]["className"] == "text-2xl"

    # Button recursion sanitized
    assert validated["children"][1]["children"][0]["props"]["className"] == "bg-blue-500 hover:bg-blue-700"


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
