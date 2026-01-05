import json
import logging
from typing import Dict, Any, List, Set

logger = logging.getLogger(__name__)

class ReactCodeGenerator:
    """Generate modern React code from schema with proper nesting support"""
    
    # ADDED "Label" to this list
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
    
    def __init__(self, schema: Dict[str, Any], component_name: str = "GeneratedUI"):
        self.schema = schema
        self.component_name = component_name
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
        
        # 1. Scan for Shadcn Components
        if node_type in self.COMPONENT_IMPORTS:
            self.used_components.add(node_type)
        
        # 2. Scan for Icons (NEW LOGIC)
        # Case A: {"type": "Icon", "props": {"name": "Mail"}}
        if node_type == "Icon":
            icon_name = node.get("props", {}).get("name")
            if icon_name:
                self.used_icons.add(icon_name)
        
        # Case B: {"type": "Button", "props": {"icon": "Mail"}} (Legacy support)
        props = node.get("props", {})
        if "icon" in props:
            self.used_icons.add(props["icon"])
        
        children = node.get("children", [])
        for child in children:
            if isinstance(child, dict):
                self._scan_for_imports(child)
    
    def _generate_imports(self) -> str:
        """Generate import statements"""
        imports = ["import React from 'react';"]
        
        # Assumes a barrel file exists at @/components/ui/index.ts
        if self.used_components:
            components = sorted(list(self.used_components))
            imports.append(f"import {{ {', '.join(components)} }} from '@/components/ui';")
        
        if self.used_icons:
            icons = sorted(list(self.used_icons))
            imports.append(f"import {{ {', '.join(icons)} }} from 'lucide-react';")
        
        return "\n".join(imports)
    
    def _replace_bg_white(self, className: str, node_type: str = "") -> str:
        """Replace bg-white with gradients to reduce white overuse"""
        if not className:
            return className
        
        # Replace bg-white with appropriate gradients based on component type
        if "bg-white" in className and "bg-gradient" not in className:
            # For hero sections, use more colorful gradient
            if node_type == "Hero":
                className = className.replace("bg-white", "bg-gradient-to-br from-blue-50 via-white to-purple-50")
            # For cards, use subtle gradient
            elif node_type == "Card":
                className = className.replace("bg-white", "bg-gradient-to-br from-white to-gray-50")
            # For timeline items, use subtle gradient
            elif node_type == "TimelineItem":
                className = className.replace("bg-white", "bg-gradient-to-br from-white to-gray-50")
            # For timeline container, usually no bg needed but if present use subtle
            elif node_type == "Timeline":
                className = className.replace("bg-white", "bg-gradient-to-br from-white to-gray-50")
            # For root, use page-level gradient
            elif node_type == "Root":
                className = className.replace("bg-white", "bg-gradient-to-br from-gray-50 via-white to-slate-50")
            # Default: subtle gradient
            else:
                className = className.replace("bg-white", "bg-gradient-to-br from-white to-gray-50")
        
        return className
    
    def _render_component(self, node: Dict[str, Any], indent: int = 1) -> str:
        """Recursively render component tree"""
        space = "  " * indent
        node_type = node.get("type", "div")
        props = node.get("props", {})
        children = node.get("children", [])
        content = node.get("content", "")
        
        # Extract props
        className = props.get("className", "")
        # Replace bg-white with gradients based on component type
        className = self._replace_bg_white(className, node_type)
        id_attr = props.get("id", "")
        # Specific props
        src = props.get("src", "")
        alt = props.get("alt", "")
        href = props.get("href", "")
        placeholder = props.get("placeholder", "")
        type_attr = props.get("type", "") # for input type="email"
        
        # Build attribute strings
        class_attr = f' className="{className}"' if className else ""
        id_attr_str = f' id="{id_attr}"' if id_attr else ""
        
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
        
        # Default to mapped tag or lowercase node_type
        html_tag = type_map.get(node_type, node_type)
        
        # --- RENDER LOGIC ---

        # 1. Icons (NEW)
        if node_type == "Icon":
            icon_name = props.get("name", "HelpCircle")
            return f'{space}<{icon_name}{class_attr} />'

        # 2. Text (Handle mixed content)
        elif node_type == "Text":
            tag = props.get("tag", "p")
            if children:
                children_html = "".join(self._render_inline_component(child, indent) for child in children)
                return f'{space}<{tag}{class_attr}{id_attr_str}>\n{children_html}\n{space}</{tag}>'
            else:
                return f'{space}<{tag}{class_attr}{id_attr_str}>{content}</{tag}>'
        
        # 3. Inputs
        elif node_type == "Input":
            placeholder_attr = f' placeholder="{placeholder}"' if placeholder else ""
            type_attr_str = f' type="{type_attr}"' if type_attr else ""
            return f'{space}<Input{class_attr}{placeholder_attr}{type_attr_str}{id_attr_str} />'
        
        # 4. Images
        elif node_type == "Image":
            return f'{space}<img src="{src}" alt="{alt}"{class_attr}{id_attr_str} />'
        
        # 5. Buttons (Handle explicit content vs children)
        elif node_type == "Button":
            if children:
                children_html = self._render_children(children, indent + 1)
                return f'{space}<Button{class_attr}{id_attr_str}>\n{children_html}\n{space}</Button>'
            return f'{space}<Button{class_attr}{id_attr_str}>{content}</Button>'

        # 6. Links
        elif node_type == "Link" or node_type == "Link/A":
            href_attr = f' href="{href}"' if href else ' href="#"'
            if children:
                children_html = self._render_children(children, indent + 1)
                return f'{space}<a{href_attr}{class_attr}{id_attr_str}>\n{children_html}\n{space}</a>'
            return f'{space}<a{href_attr}{class_attr}{id_attr_str}>{content}</a>'

        # 7. Hero, Timeline, TimelineItem (render as divs with special styling)
        elif node_type == "Hero":
            # Hero gets special default styling if bg- not present (className already has bg-white replaced)
            if "bg-" not in className:
                if className:
                    className = f"{className} bg-gradient-to-br from-blue-50 via-white to-purple-50 rounded-2xl shadow-lg p-12"
                else:
                    className = "bg-gradient-to-br from-blue-50 via-white to-purple-50 rounded-2xl shadow-lg p-12"
            elif "rounded" not in className:
                className = f"{className} rounded-2xl shadow-lg p-12"
            class_attr = f' className="{className}"'
            children_html = self._render_children(children, indent + 1)
            return f'{space}<div{class_attr}{id_attr_str}>\n{children_html}\n{space}</div>'
        
        elif node_type == "Timeline":
            # Timeline gets special default styling (className already processed)
            if "border-l" not in className:
                if className:
                    className = f"{className} relative pl-8 border-l-2 border-blue-200 space-y-8"
                else:
                    className = "relative pl-8 border-l-2 border-blue-200 space-y-8"
            class_attr = f' className="{className}"'
            children_html = self._render_children(children, indent + 1)
            return f'{space}<div{class_attr}{id_attr_str}>\n{children_html}\n{space}</div>'
        
        elif node_type == "TimelineItem":
            # TimelineItem gets special styling with dot indicator
            # Ensure it has a gradient background if bg-white was replaced
            if not className or "bg-" not in className:
                if className:
                    className = f"{className} bg-gradient-to-br from-white to-gray-50 rounded-lg p-6 shadow-md border border-gray-200"
                else:
                    className = "bg-gradient-to-br from-white to-gray-50 rounded-lg p-6 shadow-md border border-gray-200"
            class_attr = f' className="{className}"'
            children_html = self._render_children(children, indent + 1)
            # Wrap in a container with the dot
            return f'{space}<div className="relative">\n{space}  <div className="absolute -left-[2.1rem] top-0 w-4 h-4 bg-blue-500 rounded-full border-4 border-white shadow-md"></div>\n{space}  <div{class_attr}{id_attr_str}>\n{children_html}\n{space}  </div>\n{space}</div>'
        
        # 8. Generic Container / Shadcn Components
        # If it has children, render them
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
        node_type = node.get("type", "span")
        props = node.get("props", {})
        content = node.get("content", "")
        children = node.get("children", [])
        
        className = props.get("className", "")
        tag = props.get("tag", "span")
        class_attr = f' className="{className}"' if className else ""
        
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
                lines.append(f"{space}{child}")
        return "\n".join(lines)