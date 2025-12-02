from pathlib import Path
import json
import logging
import time
import requests
from typing import Optional, Dict, Any
from django.conf import settings
from functools import wraps

logger = logging.getLogger(__name__)


class ReactCodeGenerator:
    """Generate production-ready React code from schema"""
    
    # Component imports mapping
    COMPONENT_IMPORTS = {
        "Button": "from shadcn/ui",
        "Input": "from shadcn/ui",
        "Select": "from shadcn/ui",
        "Badge": "from shadcn/ui",
        "Card": "from shadcn/ui",
        "Separator": "from shadcn/ui",
    }
    
    def __init__(self, schema: Dict[str, Any], component_name: str = "GeneratedUI"):
        self.schema = schema
        self.component_name = component_name
        self.used_components = set()
        self.used_icons = set()
    
    def generate(self) -> str:
        """Generate complete React component"""
        self._scan_for_imports(self.schema)
        
        imports = self._generate_imports()
        component_body = self._render_component(self.schema, indent=2)
        
        return f"""{imports}

export default function {self.component_name}() {{
  return (
{component_body}
  );
}}
"""
    
    def _scan_for_imports(self, node: Dict[str, Any]):
        """Scan schema to determine required imports"""
        node_type = node.get("type")
        if node_type in self.COMPONENT_IMPORTS:
            self.used_components.add(node_type)
        
        if "metadata" in node and "icon" in node["metadata"]:
            self.used_icons.add(node["metadata"]["icon"])
        
        for child in node.get("children", []):
            if isinstance(child, dict):
                self._scan_for_imports(child)
    
    def _generate_imports(self) -> str:
        """Generate import statements"""
        imports = ["import React from 'react';"]
        
        # shadcn/ui imports
        if self.used_components:
            components = sorted(list(self.used_components))
            imports.append(f"import {{ {', '.join(components)} }} from '@/components/ui';")
        
        # lucide-react imports
        if self.used_icons:
            icons = sorted(list(self.used_icons))
            imports.append(f"import {{ {', '.join(icons)} }} from 'lucide-react';")
        
        return "\n".join(imports)
    
    def _render_component(self, node: Dict[str, Any], indent: int = 2) -> str:
        """Recursively render component"""
        space = " " * indent
        node_type = node.get("type")
        props = node.get("props", {})
        children = node.get("children", [])
        content = node.get("content", "")
        
        className = props.get("className", "")
        id_attr = f' id="{props.get("id")}"' if props.get("id") else ""
        class_attr = f' className="{className}"' if className else ""
        
        # Semantic HTML mapping
        semantic_map = {
            "Root": "main",
            "Section": "section",
            "Card": "div",  # Use shadcn Card component
            "Grid": "div",
            "Flex": "div",
        }
        
        tag = semantic_map.get(node_type, "div")
        
        # Handle different component types
        if node_type == "Text":
            tag = "p" if not content.startswith("#") else "h2"
            return f'{space}<{tag}{class_attr}>{content}</{tag}>'
        
        elif node_type == "Button":
            return f'{space}<Button{class_attr}{id_attr}>{content}</Button>'
        
        elif node_type == "Input":
            placeholder = props.get("placeholder", "")
            return f'{space}<Input{class_attr} placeholder="{placeholder}" />'
        
        elif node_type == "Select":
            return f'{space}<Select><SelectTrigger><SelectValue /></SelectTrigger></Select>'
        
        elif node_type == "Image":
            src = props.get("src", "")
            alt = props.get("alt", "Image")
            return f'{space}<img src="{src}" alt="{alt}" {class_attr} />'
        
        elif node_type == "Icon":
            icon_name = node.get("metadata", {}).get("icon", "AlertCircle")
            return f'{space}<{icon_name} {class_attr} />'
        
        elif node_type == "Card":
            children_html = self._render_children(children, indent + 2)
            return f'{space}<Card{class_attr}>\n{children_html}\n{space}</Card>'
        
        elif node_type == "Badge":
            return f'{space}<Badge{class_attr}>{content}</Badge>'
        
        else:
            # Default: container with children
            if children:
                children_html = self._render_children(children, indent + 2)
                return f'{space}<{tag}{class_attr}{id_attr}>\n{children_html}\n{space}</{tag}>'
            else:
                return f'{space}<{tag}{class_attr}{id_attr}>{content}</{tag}>'
    
    def _render_children(self, children: list, indent: int) -> str:
        """Render array of children"""
        lines = []
        for child in children:
            if isinstance(child, dict):
                lines.append(self._render_component(child, indent))
            elif isinstance(child, str):
                space = " " * indent
                lines.append(f"{space}{child}")
        
        return "\n".join(lines)