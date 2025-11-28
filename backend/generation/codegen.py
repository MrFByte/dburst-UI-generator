def render_node(node: dict, indent: int = 2) -> list[str]:
    """
    Convert Tailwind schema → JSX recursively.
    """
    space = " " * indent
    node_type = node.get("type")
    class_name = node.get("class", "")
    props = node.get("props", {})
    children = node.get("children", [])
    content = node.get("content", "")

    # Shared helper
    class_attr = f' className="{class_name}"' if class_name else ""

    # Component mappings
    if node_type == "Container":
        tag = "div"
        lines = [f"{space}<{tag}{class_attr}>"]
        for child in children:
            lines.extend(render_node(child, indent + 2))
        lines.append(f"{space}</{tag}>")
        return lines

    if node_type == "Text":
        return [f'{space}<p{class_attr}>{content}</p>']

    if node_type == "Button":
        return [f'{space}<button{class_attr}>{content}</button>']

    if node_type == "Input":
        placeholder = props.get("placeholder", "")
        ph_attr = f' placeholder="{placeholder}"'
        return [f'{space}<input{class_attr}{ph_attr} />']

    if node_type == "Grid":
        cols = props.get("cols", 2)
        grid_class = f"grid grid-cols-{cols} {class_name}".strip()
        lines = [f'{space}<div className="{grid_class}">']
        for child in children:
            lines.extend(render_node(child, indent + 2))
        lines.append(f"{space}</div>")
        return lines

    if node_type == "Card":
        lines = [f"{space}<div{class_attr}>"]
        for child in children:
            lines.extend(render_node(child, indent + 2))
        lines.append(f"{space}</div>")
        return lines

    # Fallback
    return [f'{space}<div{class_attr}>Unknown type: {node_type}</div>']


def schema_to_react_component(schema: dict, component_name="GeneratedUI") -> str:
    jsx_lines = render_node(schema, indent=6)
    jsx = "\n".join(jsx_lines)

    return f"""
import React from 'react';

export default function {component_name}() {{
  return (
{jsx}
  );
}}
"""
