import re
from typing import Set, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Component types allowed in schema - EXPANDED
ALLOWED_COMPONENT_TYPES = {
    # Container Components
    "Root", "Section", "Container", "Card", "Grid", "Flex", "Div", "container",
    
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

# Whitelist of safe Tailwind class prefixes
SAFE_TAILWIND_CLASSES = {
    # Spacing
    "p-", "px-", "py-", "pt-", "pb-", "pl-", "pr-",
    "m-", "mx-", "my-", "mt-", "mb-", "ml-", "mr-",
    "gap-", "space-x-", "space-y-",
    
    # Layout
    "flex", "grid", "hidden", "block", "inline-block", "inline-flex",
    "inline-grid", "absolute", "relative", "fixed", "sticky",
    
    # Flexbox & Grid
    "flex-row", "flex-col", "flex-wrap", "flex-nowrap",
    "items-", "justify-", "content-", "self-",
    "grid-cols-", "grid-rows-", "col-span-", "row-span-",
    "col-start-", "col-end-", "row-start-", "row-end-",
    "auto-cols-", "auto-rows-",
    
    # Sizing
    "w-", "h-", "min-w-", "max-w-", "min-h-", "max-h-",
    
    # Colors
    "bg-", "text-", "border-", "ring-", "fill-", "stroke-",
    
    # Typography
    "font-", "text-", "leading-", "tracking-", "line-clamp-",
    "uppercase", "lowercase", "capitalize", "normal-case",
    "italic", "not-italic", "underline", "line-through", "no-underline",
    
    # Borders
    "border-", "rounded-", "divide-",
    
    # Effects
    "shadow-", "opacity-", "mix-blend-", "bg-blend-",
    
    # Transitions & Animations
    "transition-", "duration-", "ease-", "delay-",
    "animate-", "transform", "scale-", "rotate-", "translate-",
    "skew-",
    
    # Interactivity
    "cursor-", "select-", "resize-", "pointer-events-",
    
    # Display utilities
    "overflow-", "truncate", "whitespace-",
    
    # Position
    "top-", "right-", "bottom-", "left-", "inset-", "z-",
    
    # Accessibility
    "sr-only", "not-sr-only",
    
    # Gradients (CRITICAL for modern UI)
    "from-", "via-", "to-",
    
    # Image behavior
    "object-", "aspect-",
    
    # Backdrop / Glassmorphism
    "backdrop-", "backdrop-blur-", "backdrop-filter",
    
    # Lists
    "list-",
    
    # SVG/Icon specific
    "stroke-", "fill-",
    
    # Specific borders
    "border-t-", "border-b-", "border-l-", "border-r-",
    "divide-x-", "divide-y-",
}

# State modifiers
STATE_MODIFIERS = {
    "hover", "focus", "active", "disabled", "visited",
    "focus-within", "focus-visible", "checked", "group-hover",
    "group-focus", "peer-focus", "peer-checked"
}

# Responsive prefixes
RESPONSIVE_PREFIXES = {
    "sm", "md", "lg", "xl", "2xl"
}


class SchemaValidator:
    """Validate and sanitize generated schemas"""
    
    @staticmethod
    def validate(schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate schema structure and content
        
        Args:
            schema: Component schema dictionary
            
        Returns:
            Validated and sanitized schema
            
        Raises:
            ValueError: If schema is invalid
        """
        if not isinstance(schema, dict):
            raise ValueError("Schema must be a dictionary")
        
        if "type" not in schema:
            # Auto-repair: treat string-only node as Text
            if "content" in schema:
                schema["type"] = "Text"
            else:
                logger.error(f"Schema node missing 'type': {schema}")
                raise ValueError("Schema must have 'type' field")
        
        component_type = schema["type"]
        
        # Allow both capitalized and lowercase component types
        if component_type not in ALLOWED_COMPONENT_TYPES:
            # Try to normalize the type
            normalized_type = SchemaValidator._normalize_component_type(component_type)
            if normalized_type:
                logger.info(f"Normalized component type '{component_type}' to '{normalized_type}'")
                schema["type"] = normalized_type
            else:
                # Log warning but don't fail - allow unknown types to pass through
                logger.warning(
                    f"Unknown component type: {component_type}. "
                    f"Allowing it to pass through."
                )
        
        # Validate and sanitize props
        if "props" in schema:
            if not isinstance(schema["props"], dict):
                raise ValueError("Props must be a dictionary")
            
            # Sanitize className
            if "className" in schema["props"]:
                schema["props"]["className"] = SchemaValidator._sanitize_classname(
                    schema["props"]["className"]
                )
            
            # Validate other props
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
                        validated_children.append(SchemaValidator.validate(child))
                    elif isinstance(child, str):
                        # Allow string children (text content)
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
                # Already handled in main validate method
                validated[key] = value
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
    def _sanitize_classname(classname: str) -> str:
        """
        Sanitize Tailwind className to prevent injection
        
        Args:
            classname: Space-separated class names
            
        Returns:
            Sanitized class string
        """
        if not classname or not isinstance(classname, str):
            return ""
        
        classes = classname.split()
        safe_classes = []
        
        for cls in classes:
            if SchemaValidator._is_safe_class(cls):
                safe_classes.append(cls)
            else:
                logger.warning(f"Removed potentially unsafe class: {cls}")
        
        return " ".join(safe_classes)
    
    @staticmethod
    def _is_safe_class(cls: str) -> bool:
        """
        Check if a class is safe to use
        
        Args:
            cls: Single class name
            
        Returns:
            True if safe, False otherwise
        """
        # Handle state modifiers (hover:, focus:, etc.)
        parts = cls.split(":")
        
        if len(parts) > 1:
            # Has prefix (responsive or state modifier)
            prefix = parts[0]
            base_class = ":".join(parts[1:])
            
            # Check if prefix is valid
            if prefix not in RESPONSIVE_PREFIXES and prefix not in STATE_MODIFIERS:
                return False
            
            # Recursively check base class
            return SchemaValidator._is_safe_class(base_class)
        
        # No prefix, check against allowed classes
        # Check if class starts with any safe prefix
        for safe_prefix in SAFE_TAILWIND_CLASSES:
            if cls.startswith(safe_prefix) or cls == safe_prefix.rstrip("-"):
                return True
        
        # Check exact matches for utilities without prefixes
        exact_matches = {
            "flex", "grid", "hidden", "block", "inline", "absolute", "relative",
            "fixed", "sticky", "static", "truncate", "uppercase", "lowercase",
            "capitalize", "italic", "underline", "line-through", "no-underline",
            "sr-only", "not-sr-only", "transform", "transition"
        }
        
        return cls in exact_matches
    
    def enforce_fixed_image(schema: dict):
        FIXED_IMAGE = "https://res.cloudinary.com/djv9jwwem/image/upload/v1765708366/Your_paragraph_text_2_twgtax.png"

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