import re
from typing import Set
import json
import logging
import time
import requests
from typing import Optional, Dict, Any
from django.conf import settings
from functools import wraps

logger = logging.getLogger(__name__)

ALLOWED_COMPONENT_TYPES = {
    "Root", "Section", "Card", "Grid", "Flex",
    "Text", "Button", "Input", "Textarea", "Select",
    "Image", "Badge", "Skeleton", "Separator", "Icon",
    "Link", "Link/A","Form", "Label", "List", "ListItem",
}

# Whitelist of safe Tailwind classes (prevent injection)
SAFE_TAILWIND_CLASSES = {
    # Spacing
    "p", "px", "py", "m", "mx", "my", "gap", "space-x", "space-y",
    # Layout
    "flex", "grid", "hidden", "block", "inline", "absolute", "relative",
    # Grid
    "grid-cols", "col-span", "row-span",
    # Sizing
    "w", "h", "min-w", "max-w", "min-h", "max-h",
    # Colors
    "bg", "text", "border", "shadow", "fill", "stroke",
    # Typography
    "font", "text-lg", "text-xl", "text-2xl", "font-bold", "font-semibold",
    "leading", "tracking", "uppercase", "lowercase", "capitalize",
    # Positioning
    "top", "right", "bottom", "left",
    # Transform & Transitions
    "transform", "transition", "scale", "rotate", "skew", "hover", "focus",
    # Alignment
    "items", "justify", "content", "align",
    # Display
    "rounded", "border", "opacity",
    
    "shadow", "ring", "outline", "z", "cursor",
"transition", "duration", "ease", "animate", "transform",
}


class SchemaValidator:
    """Validate and sanitize generated schemas"""
    
    @staticmethod
    def validate(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate schema structure and content"""
        if not isinstance(schema, dict):
            raise ValueError("Schema must be a dictionary")
        
        if "type" not in schema:
            raise ValueError("Schema must have 'type' field")
        
        component_type = schema["type"]
        if component_type not in ALLOWED_COMPONENT_TYPES:
            raise ValueError(f"Unknown component type: {component_type}")
        
        # Sanitize className
        if "props" in schema and "className" in schema["props"]:
            schema["props"]["className"] = SchemaValidator._sanitize_classname(
                schema["props"]["className"]
            )
        
        # Recursively validate children
        if "children" in schema and isinstance(schema["children"], list):
            schema["children"] = [
                SchemaValidator.validate(child) for child in schema["children"]
            ]
        
        return schema
    
    @staticmethod
    def _sanitize_classname(classname: str) -> str:
        """Remove potentially harmful classes"""
        if not classname:
            return ""
        
        classes = classname.split()
        safe_classes = []
        
        for cls in classes:
            # Allow responsive prefixes and state modifiers
            if any(cls.startswith(prefix + ":") for prefix in 
                   ["sm", "md", "lg", "xl", "2xl", "hover", "focus", "active", "group"]):
                base_class = cls.split(":")[-1]
            else:
                base_class = cls
            
            # Check if class starts with allowed prefix
            if any(base_class.startswith(prefix) for prefix in SAFE_TAILWIND_CLASSES):
                safe_classes.append(cls)
        
        return " ".join(safe_classes)