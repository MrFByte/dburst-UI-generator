import pytest
from generation.codegen import ReactCodeGenerator


def test_scan_imports_detects_components_and_icons():
    schema = {
        "type": "Button",
        "props": {"className": "bg-blue"},
        "metadata": {"icon": "Rocket"},
        "children": []
    }

    gen = ReactCodeGenerator(schema)
    gen._scan_for_imports(schema)

    assert "Button" in gen.used_components
    assert "Rocket" in gen.used_icons


def test_generate_imports_output():
    schema = {"type": "Button"}
    gen = ReactCodeGenerator(schema)
    gen.used_components = {"Button"}
    gen.used_icons = {"Rocket"}

    imports = gen._generate_imports()

    assert "import React from 'react'" in imports
    assert "import { Button } from '@/components/ui'" in imports
    assert "import { Rocket } from 'lucide-react'" in imports


def test_render_text_component():
    schema = {
        "type": "Text",
        "content": "Hello World",
        "props": {"className": "text-lg"}
    }

    gen = ReactCodeGenerator(schema)
    html = gen._render_component(schema, indent=2)

    assert '<p className="text-lg">Hello World</p>' in html


def test_render_button_component():
    schema = {
        "type": "Button",
        "content": "Click Me",
        "props": {"className": "btn-primary"}
    }

    gen = ReactCodeGenerator(schema)
    html = gen._render_component(schema, indent=2)

    assert '<Button className="btn-primary">Click Me</Button>' in html


def test_render_nested_children():
    schema = {
        "type": "Section",
        "props": {"className": "p-4"},
        "children": [
            {"type": "Text", "content": "Hello", "props": {}},
            {"type": "Button", "content": "Click", "props": {}}
        ]
    }

    gen = ReactCodeGenerator(schema)
    html = gen._render_component(schema, indent=2)

    # root
    assert "<section className=\"p-4\">" in html

    # children
    assert "<p>Hello</p>" in html
    assert "<Button>Click</Button>" in html


def test_card_renders_children():
    schema = {
        "type": "Card",
        "props": {"className": "shadow"},
        "children": [
            {"type": "Text", "content": "Card Title", "props": {}}
        ]
    }

    gen = ReactCodeGenerator(schema)
    html = gen._render_component(schema, indent=2)

    assert "<Card className=\"shadow\">" in html
    assert "<p>Card Title</p>" in html
    assert "</Card>" in html


def test_generate_full_component():
    schema = {
        "type": "Button",
        "content": "Submit",
        "props": {}
    }

    gen = ReactCodeGenerator(schema, component_name="MyComponent")
    output = gen.generate()

    assert "export default function MyComponent()" in output
    assert "<Button>Submit</Button>" in output
    assert "import React from 'react'" in output
    assert "import { Button } from '@/components/ui'" in output
