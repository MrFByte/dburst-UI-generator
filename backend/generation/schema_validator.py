import re
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)

# Component types allowed in schema - EXPANDED
ALLOWED_COMPONENT_TYPES = {
    # Container Components
    "Root", "Section", "Container", "Card", "Grid", "Flex", "Div", "container",
    
    # Special Layout Components
    "Hero", "Timeline", "TimelineItem",
    
    # Card Sub-components (CRITICAL - was missing!)
    "CardHeader", "CardContent", "CardFooter", "CardTitle", "CardDescription",
    
    # Table Components
    "Table", "TableHeader", "TableBody", "TableRow", "TableCell", "TableHead",
    
    # Chart Components
    "LineChart", "BarChart", "DonutChart", "PieChart", "AreaChart",
    
    # Form Components
    "Form", "Label", "Input", "Textarea", "Select",
    
    # Content Components
    "Text", "Image", "Icon", "Badge", "Separator",
    
    # Interactive Components
    "Button", "Link", "Link/A",
    
    # List Components
    "List", "ListItem",
    
    # Loading Components
    "Skeleton",
    
    # Layout Components
    "Header", "Footer", "Nav", "Aside", "Main", "Article",
    
    # Generic HTML elements (fallback)
    "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "img", "ul", "ol", "li", "section", "article", "nav",
    "header", "footer", "main", "aside", "table", "tbody", "thead", "tr", "td", "th"
}

# Limits that keep a malicious or runaway schema from blowing up codegen
# (recursion) or the response size.
MAX_SCHEMA_DEPTH = 50
MAX_SCHEMA_NODES = 2000
MAX_CLASSNAME_LENGTH = 2000

# Fallback for Image nodes without a usable src (see enforce_fixed_image).
FIXED_IMAGE = "https://res.cloudinary.com/djv9jwwem/image/upload/v1765708366/Your_paragraph_text_2_twgtax.png"

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f-\x9f]")


class SchemaValidator:
    """Validate and sanitize generated schemas"""
    
    @staticmethod
    def validate(schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate schema structure and normalize it in place.

        This is structural validation only. Output safety (escaping, URL
        schemes, tag/icon names) is ReactCodeGenerator's job, so it holds for
        every schema that reaches codegen, validated or not.

        Args:
            schema: Component schema dictionary

        Returns:
            Validated schema

        Raises:
            ValueError: If schema is invalid or exceeds the depth/node limits
        """
        return SchemaValidator._validate_node(schema, depth=1, counter=[0])

    @staticmethod
    def _validate_node(schema: Dict[str, Any], depth: int, counter: List[int]) -> Dict[str, Any]:
        if not isinstance(schema, dict):
            raise ValueError("Schema must be a dictionary")
        if depth > MAX_SCHEMA_DEPTH:
            raise ValueError(f"Schema exceeds maximum depth of {MAX_SCHEMA_DEPTH}")
        counter[0] += 1
        if counter[0] > MAX_SCHEMA_NODES:
            raise ValueError(f"Schema exceeds maximum of {MAX_SCHEMA_NODES} nodes")

        if "type" not in schema:
            # Auto-repair: treat string-only node as Text
            if "content" in schema:
                schema["type"] = "Text"
            else:
                logger.error(f"Schema node missing 'type': {schema}")
                raise ValueError("Schema must have 'type' field")

        component_type = schema["type"]
        if not isinstance(component_type, str) or not component_type:
            raise ValueError("Schema 'type' must be a non-empty string")

        # Allow both capitalized and lowercase component types
        if component_type not in ALLOWED_COMPONENT_TYPES:
            # Try to normalize the type
            normalized_type = SchemaValidator._normalize_component_type(component_type)
            if normalized_type:
                logger.info(f"Normalized component type '{component_type}' to '{normalized_type}'")
                schema["type"] = normalized_type
            else:
                # Log warning but don't fail - allow unknown types to pass through
                # (codegen only emits it as a tag if it's a safe identifier)
                logger.warning(
                    f"Unknown component type: {component_type}. "
                    f"Allowing it to pass through."
                )

        # Validate props
        if "props" in schema:
            if not isinstance(schema["props"], dict):
                raise ValueError("Props must be a dictionary")
            schema["props"] = SchemaValidator._validate_props(schema["props"], component_type)

        # Validate content (if present)
        if "content" in schema:
            if not isinstance(schema["content"], str):
                schema["content"] = str(schema["content"])

        # Recursively validate children
        if "children" in schema:
            if isinstance(schema["children"], list):
                validated_children = []
                for child in schema["children"]:
                    if isinstance(child, dict):
                        validated_children.append(
                            SchemaValidator._validate_node(child, depth + 1, counter)
                        )
                    elif isinstance(child, str):
                        # Allow string children (text content)
                        counter[0] += 1
                        if counter[0] > MAX_SCHEMA_NODES:
                            raise ValueError(f"Schema exceeds maximum of {MAX_SCHEMA_NODES} nodes")
                        validated_children.append(child)
                    else:
                        logger.warning(f"Skipping invalid child type: {type(child)}")
                schema["children"] = validated_children
            else:
                raise ValueError("Children must be a list")

        return schema

    @staticmethod
    def _normalize_component_type(component_type: str) -> str:
        """
        Normalize component type to allowed format
        
        Args:
            component_type: Original component type
            
        Returns:
            Normalized type or empty string if not found
        """
        # Direct match
        if component_type in ALLOWED_COMPONENT_TYPES:
            return component_type
        
        # Try lowercase
        if component_type.lower() in ALLOWED_COMPONENT_TYPES:
            return component_type.lower()
        
        # Try capitalized
        capitalized = component_type.capitalize()
        if capitalized in ALLOWED_COMPONENT_TYPES:
            return capitalized
        
        # Special cases mapping
        type_mapping = {
            "Container": "Container",
            "container": "Container",
            # FIX: Don't force flex on standard divs
            "Div": "div", 
            "div": "div",
            "Box": "div", # Box is usually just a block
            
            # Map Flex explicitly
            "Flex": "Flex",
            "Row": "Flex", # AI often calls flex rows "Row"
            "Column": "Flex",
            
            # Text mappings
            "Span": "span",
            "Paragraph": "Text",
            "Heading": "Text",
            
            # Link/Image
            "A": "Link/A",
            "Link": "Link/A", # Normalize to your internal name
            "Img": "Image",
            
            # Lists
            "Ul": "List",
            "Ol": "List",
            "Li": "ListItem",
            
            # Shadcn Cards (Case insensitivity handling)
            "cardheader": "CardHeader",
            "cardcontent": "CardContent",
            "cardfooter": "CardFooter",
            "cardtitle": "CardTitle",
            "carddescription": "CardDescription",
        }
        
        return type_mapping.get(component_type, "")
    
    @staticmethod
    def _validate_props(props: Dict[str, Any], component_type: str) -> Dict[str, Any]:
        """
        Validate component props
        
        Args:
            props: Component props dictionary
            component_type: Type of component
            
        Returns:
            Validated props
        """
        validated = {}
        
        for key, value in props.items():
            if key == "className":
                validated[key] = SchemaValidator._clean_classname(value)
            elif key == "id":
                # Validate ID (alphanumeric, hyphens, underscores only)
                if isinstance(value, str) and re.match(r'^[a-zA-Z0-9_-]+$', value):
                    validated[key] = value
                else:
                    logger.warning(f"Invalid id prop: {value}")
            elif key == "tag":
                # Validate semantic tag
                allowed_tags = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "span", "div", "ul", "ol", "li"}
                if value in allowed_tags:
                    validated[key] = value
                else:
                    logger.warning(f"Invalid tag prop: {value}")
            elif key in {"src", "href", "alt", "placeholder", "icon"}:
                # Allow string props for images, links, etc.
                validated[key] = str(value) if value else ""
            elif key in {"disabled", "required", "checked"}:
                # Boolean props
                validated[key] = bool(value)
            else:
                # Allow other props (for extensibility)
                validated[key] = value
        
        return validated
    
    @staticmethod
    def _clean_classname(classname: Any) -> str:
        """
        Normalize a className string. Classes are passed through untouched:
        the preview has a full Tailwind build, and injection is prevented by
        codegen escaping rather than by a class whitelist.
        """
        if not isinstance(classname, str):
            return ""
        classname = _CONTROL_CHARS.sub(" ", classname)
        classname = " ".join(classname.split())
        if len(classname) > MAX_CLASSNAME_LENGTH:
            # Cut at a class boundary rather than mid-class.
            classname = classname[:MAX_CLASSNAME_LENGTH].rsplit(" ", 1)[0]
        return classname

    @staticmethod
    def enforce_fixed_image(schema: dict):

        def walk(node):
            if isinstance(node, dict):
                if node.get("type") == "Image":
                    node.setdefault("props", {})
                    
                    current_src = node["props"].get("src", "")
                    if not current_src or "placeholder" in current_src or "example" in current_src:
                        node["props"]["src"] = FIXED_IMAGE
                        
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for i in node:
                    walk(i)

        walk(schema)