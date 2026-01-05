import json
import logging
import time
import requests
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)

GROQ_API_KEY = settings.GROQ_AI_API_KEY
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

GEMINI_API_KEY = settings.GEMINI_API_KEY
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

LLM_MODELS = {
    # UI Generation Models (user selectable)
    "ui_llama_3_3": "llama-3.3-70b-versatile",
    "ui_llama_3_1": "llama-3.1-8b-instant",
    "ui_gemini_2_5": "gemini-2.5-flash",
    "ui_gemini_2_0": "gemini-2.0-flash",
    "ui_gpt_oss_120b": "openai/gpt-oss-120b",
    
    # Planning / Reasoning Models (system controlled)
    "plan_moonshot": "moonshotai/kimi-k2-instruct-0905",
    "plan_llama_4_scout": "meta-llama/llama-4-scout-17b-16e-instruct"
}

# Default models
DEFAULT_PLANNING_MODEL = "plan_moonshot"
DEFAULT_UI_MODEL = "ui_llama_3_3"

PLANNER_SYSTEM_PROMPT = """
You are a reasoning-first UI architect.

Your responsibilities:
1. Infer intent and page category
2. Decide layout archetype
3. Decide required and forbidden UI patterns
4. Generate a design_plan JSON
5. Give a project name in 5 to 200 characters in key name project_name as string
6. Give a project description in 10 to 500 characters in key name project_description as string
7. If the page represents a product that need to showcase image:
   - Generate a list of products
   - Each product MUST include:
     { name, price, image_url }
   - image_url MUST visually represent the product
   - Decorative images are forbidden
   
You must DISCOVER the layout — not assume it.

The key "design_plan.sections" MUST always be a list of objects:
{ name: string, type: string, content: string }

Do NOT include login/signup unless explicitly requested.

RETURN ONLY VALID JSON.
"""


UI_GENERATOR_SYSTEM_PROMPT = """You are an expert React/Tailwind developer specializing in modern, polished UI design.
Your job is to convert a `design_plan` into a VALID JSON UI SCHEMA with RICH, REALISTIC CONTENT.

-------------------------------------------
STRICT OUTPUT FORMAT
-------------------------------------------
{
  "title": "Page Title",
  "schema": { ...Root Component... },
  "code": "",
  "metadata": { "framework": "react", "tailwindVersion": "3.4" }
}

-------------------------------------------
COMPONENT SCHEMA RULES
-------------------------------------------
1. Structure: {"type": "Component", "props": {...}, "children": []}
2. Text Content: Use "content": "Text" (Do not use children for raw text).
3. NO Raw HTML: Never put <tags> inside a string. Use "type": "Link" or "Text".
4. NO PLACEHOLDERS: Generate actual, realistic content based on the design plan.
5. Text should never have white color.
6. Instead of using placeholders in img src, use the links given in the prompt.

Allowed Types:
Root, Section, Container, Card, CardHeader, CardTitle, CardContent,
Form, Label, Input, Button, Text, Link, Icon, Image, Div,
Hero, Timeline, TimelineItem, Grid, Flex

-------------------------------------------
CRITICAL: GENERATE REAL CONTENT, NOT PLACEHOLDERS
-------------------------------------------
NEVER use placeholder text like "Stats Counter" or "Trophy Gallery".
ALWAYS generate:
- Actual numbers, metrics, and data points
- Realistic titles, descriptions, and labels
- Meaningful content that matches the design plan's intent
- Proper icons that match the content context

-------------------------------------------
MODERN UI PATTERNS (IMPLEMENT THESE)
-------------------------------------------

1. STATS COUNTERS:
   Structure each stat as a Card with:
   - An Icon at the top (use appropriate icon: Users, TrendingUp, Star, Award, Target, etc.)
   - A large, bold number (use text-3xl or text-4xl font-bold)
   - A descriptive label below (text-sm text-muted-foreground)
   - Modern styling: rounded-xl, shadow-md, border, bg-gradient-to-br or solid color
   - Icon should be colored (e.g., text-purple-600, text-blue-600)
   
   Example structure:
   {
     "type": "Card",
     "props": {"className": "p-6 rounded-xl shadow-md border bg-gradient-to-br from-white to-purple-50"},
     "children": [
       {"type": "Icon", "props": {"name": "Users", "className": "w-8 h-8 text-purple-600 mb-3"}},
       {"type": "Text", "props": {"className": "text-4xl font-bold text-gray-900 mb-1"}, "content": "12k+"},
       {"type": "Text", "props": {"className": "text-sm text-gray-600"}, "content": "Active Users"}
     ]
   }

2. TROPHY/AWARD GALLERIES:
   Create a responsive grid of trophy cards with:
   - Card with rounded corners and shadow
   - Trophy icon or image placeholder
   - Title text (trophy name)
   - Optional subtitle (date or achievement)
   - Hover effects suggested via className
   
   Example:
   {
     "type": "Card",
     "props": {"className": "p-6 rounded-xl shadow-md border bg-gradient-to-br from-yellow-50 to-amber-50 hover:shadow-lg transition-shadow"},
     "children": [
       {"type": "Icon", "props": {"name": "Trophy", "className": "w-12 h-12 text-yellow-600 mb-3"}},
       {"type": "Text", "props": {"className": "text-lg font-semibold text-gray-900"}, "content": "World Cup 2022"},
       {"type": "Text", "props": {"className": "text-sm text-gray-600 mt-1"}, "content": "FIFA World Cup Champion"}
     ]
   }

3. HERO SECTIONS:
   Use type "Hero" for hero sections:
   - Large, prominent heading (text-5xl or text-6xl font-bold)
   - Descriptive subtitle (text-xl text-gray-600)
   - Background gradient: bg-gradient-to-br from-blue-50 via-white to-purple-50
   - Centered or left-aligned layout
   - Generous padding (p-12 or p-16)
   - Rounded corners: rounded-2xl
   - Shadow: shadow-lg
   
   Example:
   {
     "type": "Hero",
     "props": {"className": "bg-gradient-to-br from-blue-50 via-white to-purple-50 rounded-2xl shadow-lg p-12 text-center"},
     "children": [
       {"type": "Text", "props": {"className": "text-5xl font-bold text-gray-900 mb-4"}, "content": "Lionel Messi: The Record Breaker"},
       {"type": "Text", "props": {"className": "text-xl text-gray-600"}, "content": "A legendary career marked by unparalleled achievements"}
     ]
   }

4. TIMELINES:
   Use type "Timeline" for timeline containers and "TimelineItem" for each entry:
   - Timeline container: Use "Timeline" type with relative positioning and left border
   - Each timeline item: Use "TimelineItem" type
   - Year/date prominently displayed (text-2xl font-bold)
   - Achievement description (text-sm text-gray-600)
   - Each item should be a Card with gradient background
   
   Example:
   {
     "type": "Timeline",
     "props": {"className": "relative pl-8 border-l-2 border-blue-200 space-y-8"},
     "children": [
       {
         "type": "TimelineItem",
         "props": {"className": "relative"},
         "children": [
           {"type": "Text", "props": {"className": "text-2xl font-bold text-gray-900 mb-1"}, "content": "2004"},
           {"type": "Text", "props": {"className": "text-sm text-gray-600"}, "content": "Debut for Barcelona"}
         ]
       }
     ]
   }

5. TESTIMONIAL CAROUSELS:
   - Card-based testimonials
   - Quote text in italic
   - Author name and role
   - Optional avatar icon

6. ICONS (lucide-react):
   Use appropriate icons from lucide-react. Common icons:
   - Users, User, UserCheck (for user-related stats)
   - TrendingUp, TrendingDown, BarChart (for metrics)
   - Star, Award, Trophy (for achievements)
   - Target, Goal, Zap (for performance)
   - Calendar, Clock (for time-related)
   - Mail, Phone, MessageSquare (for contact)
   - Github, Twitter, Linkedin (for social)
   - LayoutDashboard, Settings, Home (for navigation)
   - ArrowRight, ArrowLeft, ChevronRight (for navigation)
   - Check, X, AlertCircle (for status)
   
   Format: {"type": "Icon", "props": {"name": "IconName", "className": "w-6 h-6 text-purple-600"}}

7. MODERN STYLING GUIDELINES:
   - Use rounded-xl or rounded-2xl for modern card corners
   - Apply shadow-md or shadow-lg for depth
   - Use gradient backgrounds: bg-gradient-to-br from-color1 to-color2
   - Color scheme: Use purple, blue, indigo for primary actions (text-purple-600, bg-purple-50)
   - Spacing: Use p-6 or p-8 for card padding, gap-6 for grid spacing
   - Typography: Use font-bold for headings, font-semibold for subheadings
   - Text sizes: text-4xl or text-5xl for hero numbers, text-2xl for section titles
   - BACKGROUNDS: NEVER use 'bg-white' - ALWAYS use gradients:
     * Root: bg-gradient-to-br from-gray-50 via-white to-slate-50
     * Cards: bg-gradient-to-br from-white to-gray-50 (or colored variants)
     * Sections: Can use bg-gradient-to-br from-transparent to-gray-50/30 for subtle variation
   - SECTION STRUCTURE: Always wrap sections with proper padding (py-12 px-4 sm:px-6 lg:px-8)
   - CONTAINERS: Use max-w-7xl mx-auto for main containers to prevent content from stretching too wide
   - CRITICAL: If you see 'bg-white' in any example, replace it with a gradient. Pure white backgrounds are forbidden.

8. CARDS:
   Follow the Shadcn pattern:
   Card -> CardHeader (optional) -> CardContent -> CardFooter (optional).
   CRITICAL: NEVER use 'bg-white' alone. Always use gradients:
   - bg-gradient-to-br from-white to-gray-50 (subtle)
   - bg-gradient-to-br from-white to-purple-50 (for stats)
   - bg-gradient-to-br from-white to-blue-50 (for info)
   - bg-gradient-to-br from-yellow-50 to-amber-50 (for trophies/awards)
   Use: 'shadow-md', 'border border-gray-200', 'rounded-xl', 'p-6'
   For modern cards: Always add gradient backgrounds, never pure white

9. LAYOUT:
   - Use responsive grids: grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6
   - Full-width sections: w-full py-16 or py-20
   - Container max-width: max-w-7xl mx-auto px-4
   - Centered content: flex items-center justify-center

-------------------------------------------
CONTENT GENERATION RULES
-------------------------------------------
1. Read each section's "content" field carefully - it describes what should be displayed
2. Extract key information (numbers, achievements, dates) from the content description
3. Generate realistic data that matches the context (e.g., if it says "800+ goals", use "800+" not "Stats Counter")
4. Create meaningful labels and descriptions
5. Use appropriate icons that match the content theme
6. Apply modern color schemes and styling

-------------------------------------------
EXECUTION
-------------------------------------------
Read the `design_plan` provided by the user carefully. 
For each section, generate REAL CONTENT based on the section's description.
Apply modern styling, appropriate icons, and realistic data.
Ensure the final JSON is valid and nest components correctly.
DO NOT use placeholder text - always generate actual, meaningful content.
"""


class LLMClient:
    """Two-stage LLM: Strategic Planning → Precision Building"""
    
    def __init__(self, ui_model: str = None, planning_model: str = None):
        """
        Initialize client with model selection
        
        Args:
            ui_model: Model key for UI generation (e.g., 'ui_llama_3_3', 'ui_gemini_2_0')
            planning_model: Model key for planning (defaults to 'plan_moonshot')
        """
        self.ui_model_key = ui_model if ui_model else DEFAULT_UI_MODEL
        self.planning_model_key = planning_model if planning_model else DEFAULT_PLANNING_MODEL
        
        # Validate models exist
        if self.ui_model_key not in LLM_MODELS:
            raise ValueError(f"Invalid UI model: {self.ui_model_key}. Must be one of {list(LLM_MODELS.keys())}")
        if self.planning_model_key not in LLM_MODELS:
            raise ValueError(f"Invalid planning model: {self.planning_model_key}")
        
        self.ui_model = LLM_MODELS[self.ui_model_key]
        self.planning_model = LLM_MODELS[self.planning_model_key]
        
        self.timeout = 60
        
        logger.info(f"LLMClient initialized:")
        logger.info(f"  Planning model: {self.planning_model_key} ({self.planning_model})")
        logger.info(f"  UI generation model: {self.ui_model_key} ({self.ui_model})")
        
    def generate_ui(self, user_prompt: str, retries: int = 3) -> Dict[str, Any]:
        """
        Two-stage generation:
        Stage 1: Strategic design planning with planning model
        Stage 2: UI generation with selected UI model
        """
        # STAGE 1: Planning with Moonshot (or other planning model)
        logger.info("🎨 STAGE 1: Creating strategic design plan...")
        design_plan = self._call_planner(user_prompt, retries)
        
        print(design_plan)
        print(":::::::::::::::::::::: NEXT :::::::::::::::::::")
        logger.info(f"✓ Design plan complete:")
        logger.info(f"  Project: {design_plan.get('project_name', 'Unknown')}")
        logger.info(f"  Style: {design_plan.get('theme', {}).get('style', 'Unknown')}")
        logger.info(f"  Primary color: {design_plan.get('theme', {}).get('color_scheme', {}).get('primary', 'Unknown')}")
        
        # STAGE 2: UI Generation with user-selected model
        logger.info("🔨 STAGE 2: Building UI from design plan...")
        ui_prompt = self._compile_ui_prompt(design_plan)
        ui_result = self._call_ui_generator(ui_prompt, design_plan, retries)
        
        print(ui_result)
        
        logger.info("✓ UI generation complete!")
        
        return {
            "project_name": design_plan["project_name"][:200],  # Enforce max 200
            "project_description": design_plan["project_description"][:500],  # Enforce max 500
            "design_plan": design_plan,
            "title": ui_result["title"],
            "schema": ui_result["schema"],
            "metadata": ui_result["metadata"],
            "usage": {
                "planning_tokens": design_plan.get("usage", {}),
                "generation_tokens": ui_result.get("usage", {})
            },
            "models": {
                "planning": self.planning_model_key,
                "ui_generation": self.ui_model_key
            }
        }
    
    def _call_planner(self, prompt: str, retries: int) -> Dict[str, Any]:
        """Stage 1: Strategic design planning with planning model"""
        for attempt in range(retries):
            try:
                return self._call_groq_api(
                    prompt=prompt,
                    system_prompt=PLANNER_SYSTEM_PROMPT,
                    model=self.planning_model,
                    max_tokens=3500
                )
            except Exception as e:
                logger.error(f"Planner attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
    
    def _call_ui_generator(self, prompt: str, design_plan: Dict, retries: int) -> Dict[str, Any]:
        """Stage 2: UI generation with user-selected model"""
        
        # SAFELY extract nested values with defaults
        theme = design_plan.get('theme', {})
        colors = theme.get('color_scheme', {})
        typography = theme.get('typography', {})
        
        # Use .get() for design_system to prevent KeyError crash
        design_system = design_plan.get("design_system", {})
        spacing = design_system.get("spacing", "p-4 gap-4")
        radius = design_system.get("border_radius") or design_system.get("radius", "rounded-lg")

        # Get project context
        project_name = design_plan.get('project_name', '')
        project_description = design_plan.get('project_description', '')
        
        # Inject design context safely
        enhanced_prompt = f"""PROJECT CONTEXT:
Project Name: {project_name}
Project Description: {project_description}

DESIGN SPECIFICATIONS:
THEME: {theme.get('style', 'modern')}
PRIMARY COLOR: {colors.get('primary', '#000000')}
BACKGROUND: {colors.get('background', '#ffffff')}
TYPOGRAPHY SCALE: Hero: {typography.get('heading', 'text-2xl font-bold')}, Body: {typography.get('body', 'text-sm')}

SPACING SYSTEM: {spacing}
BORDER RADIUS: {radius}

BUILD INSTRUCTIONS:
{prompt}

CRITICAL REMINDERS:
1. Generate REAL CONTENT - extract actual numbers, achievements, and data from section descriptions
2. Use appropriate icons from lucide-react (see icon suggestions in sections above)
3. Apply modern styling: rounded-xl, shadow-md, gradients, proper spacing (p-6, gap-6)
4. DO NOT use placeholder text - always generate meaningful, realistic content
5. Use EXACT Tailwind classes
6. Build nested structures (Root → Section → Grid → Components)
7. Create polished, production-ready UI that matches modern design standards"""
        
        for attempt in range(retries):
            try:
                # Check if using Gemini model
                if self.ui_model_key.startswith("ui_gemini"):
                    return self._call_gemini(enhanced_prompt, UI_GENERATOR_SYSTEM_PROMPT, max_tokens=4096)
                else:
                    return self._call_groq_api(
                        prompt=enhanced_prompt,
                        system_prompt=UI_GENERATOR_SYSTEM_PROMPT,
                        model=self.ui_model,
                        max_tokens=4096
                    )
            except Exception as e:
                logger.error(f"UI Generator attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
    
    def _call_groq_api(self, prompt: str, system_prompt: str, model: str, max_tokens: int = 4096) -> Dict[str, Any]:
        """Call Groq API (supports multiple models via Groq)"""
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": max_tokens,
        }
        
        logger.info(f"Calling Groq API with model: {model}")
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=self.timeout)
        
        if response.status_code != 200:
            raise ValueError(f"Groq API Error ({response.status_code}): {response.text}")
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        
        return self._parse_response(content, usage)
    
    def _call_gemini(self, prompt: str, system_prompt: str, max_tokens: int = 4096) -> Dict[str, Any]:
        """Call Gemini API"""
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": system_prompt},
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": max_tokens,
            }
        }
        
        url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        logger.info("Calling Gemini API")
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        
        if response.status_code != 200:
            raise ValueError(f"Gemini API Error ({response.status_code}): {response.text}")
        
        data = response.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        
        return self._parse_response(content, usage)
    
    def _parse_response(self, content: str, usage: Dict) -> Dict[str, Any]:
      """Extract and validate JSON from LLM response"""
      
      # Remove markdown code blocks
      if "```json" in content:
          content = content.split("```json")[1].split("```")[0]
      elif "```" in content:
          content = content.split("```")[1].split("```")[0]

      content = content.strip()
      
      # CRITICAL FIX: Remove invalid control characters
      # Replace newlines and tabs within strings (common LLM error)
      import re
      
      # First, protect actual line breaks in the JSON structure
      # by temporarily replacing them
      lines = content.split('\n')
      cleaned_lines = []
      
      in_string = False
      for line in lines:
          # Track if we're inside a string
          clean_line = ""
          for i, char in enumerate(line):
              if char == '"' and (i == 0 or line[i-1] != '\\'):
                  in_string = not in_string
              clean_line += char
          cleaned_lines.append(clean_line)
      
      # Rejoin with newlines
      content = '\n'.join(cleaned_lines)
      
      # Remove other control characters that break JSON
      content = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', content)

      try:
          parsed = json.loads(content)
      except json.JSONDecodeError as e:
          logger.error(f"JSON Parse Error: {e}")
          logger.error(f"Content preview: {content[:500]}")
          
          # Try to fix common issues
          try:
              # Escape unescaped quotes in strings
              content = re.sub(r'(?<!\\)"(?=.*":)', r'\"', content)
              parsed = json.loads(content)
              logger.warning("Fixed JSON with quote escaping")
          except:
              raise ValueError(f"Invalid JSON from LLM: {str(e)}")

      parsed["usage"] = usage
      return parsed

    def _compile_ui_prompt(self, design_plan: Dict[str, Any]) -> str:
        archetype = design_plan.get("layout_archetype", "standard_layout")
        intent = design_plan.get("intent", "")
        required = design_plan.get("required_patterns", [])
        forbidden = design_plan.get("forbidden_patterns", [])

        design = design_plan.get("design_plan", {})
        sections = design.get("sections", [])

        lines = [
            f"PAGE INTENT: {intent}",
            f"LAYOUT ARCHETYPE: {archetype}",
            "",
            "REQUIRED UI PATTERNS:"
        ]

        for r in required:
            lines.append(f"- {r}")

        lines.append("")
        lines.append("FORBIDDEN UI PATTERNS:")
        for f in forbidden:
            lines.append(f"- {f}")

        lines.append("")
        lines.append("=" * 60)
        lines.append("DETAILED SECTIONS TO IMPLEMENT:")
        lines.append("=" * 60)
        lines.append("")
        
        # Icon mapping for different section types
        icon_suggestions = {
            "hero": ["Star", "Award", "Trophy", "Zap"],
            "stats": ["Users", "TrendingUp", "Star", "Award", "Target", "BarChart", "Zap", "Trophy"],
            "grid": ["Trophy", "Award", "Star", "Medal", "Crown"],
            "timeline": ["Calendar", "Clock", "History", "ArrowRight"],
            "carousel": ["Quote", "MessageSquare", "Users"],
            "footer": ["Github", "Twitter", "Linkedin", "Mail"]
        }
        
        for idx, section in enumerate(sections, 1):
            name = section.get("name", "unnamed")
            section_type = section.get("type", "")
            content_desc = section.get("content", "")
            
            lines.append(f"--- SECTION {idx}: {name} ({section_type}) ---")
            lines.append(f"Description: {content_desc}")
            
            # Provide implementation guidance based on section type
            if section_type == "hero":
                lines.append("Implementation: Create a full-width hero with large heading, subtitle, and optional background.")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("hero", ["Star"])))
            elif section_type == "stats":
                lines.append("Implementation: Create a grid of stat cards (typically 3-4 cards).")
                lines.append("Each card should have: Icon + Large Number + Label")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("stats", ["TrendingUp"])))
                lines.append("Extract actual numbers from the description (e.g., '800+ goals' -> display '800+')")
            elif section_type == "grid":
                lines.append("Implementation: Create a responsive grid (2-3 columns) of cards.")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("grid", ["Trophy"])))
                lines.append("Each card should represent a trophy/achievement with icon, title, and optional subtitle.")
            elif section_type == "timeline":
                lines.append("Implementation: Create a vertical or horizontal timeline with items.")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("timeline", ["Calendar"])))
                lines.append("Each item should show: Year/Date + Achievement Title + Description")
            elif section_type == "carousel":
                lines.append("Implementation: Create testimonial/quote cards in a grid or list.")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("carousel", ["Quote"])))
            elif section_type == "footer":
                lines.append("Implementation: Create a footer with links and social icons.")
                lines.append("Icons: Use one of: " + ", ".join(icon_suggestions.get("footer", ["Github"])))
            
            lines.append("")  # Empty line between sections

        lines.append("=" * 60)
        lines.append("")
        lines.append("CRITICAL INSTRUCTIONS:")
        lines.append("1. Generate REAL CONTENT - extract numbers, achievements, and data from section descriptions")
        lines.append("2. Use appropriate icons for each section type (see suggestions above)")
        lines.append("3. Apply modern styling: rounded-xl, shadow-md, gradients, proper spacing")
        lines.append("4. DO NOT use placeholder text like 'Stats Counter' or 'Trophy Gallery'")
        lines.append("5. Create meaningful titles, numbers, and labels based on the content descriptions")
        lines.append("6. Do NOT invent additional sections beyond those listed above")
        lines.append("7. Do NOT include authentication UI unless explicitly allowed")
        lines.append("8. Build a polished, production-ready UI that matches modern design standards")

        return "\n".join(lines)