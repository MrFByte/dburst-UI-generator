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

PLANNER_SYSTEM_PROMPT = """You are a world-class UI/UX design strategist.
Your goal is to analyze a user request and produce a comprehensive DESIGN PLAN JSON.

RETURN ONLY VALID JSON.

CORE INSTRUCTION:
1. Analyze if the request is for a Dashboard/Data App OR a Landing/Auth Page.
2. Adapt the 'layout_plan' and 'components' strictly to that use case.

JSON STRUCTURE:
{
  "project_name": "String",
  "project_description": "String",
  "concept": "String",
  "theme": {
    "style": "modern | minimal | dashboard",
    "color_scheme": {
      "primary": "Hex",
      "secondary": "Hex",
      "background": "Hex",
      "surface": "Hex",
      "text": "Hex"
    },
    "typography": {
      "heading": "Tailwind classes",
      "body": "Tailwind classes"
    }
  },
  
  "design_system": {              <--- ADD THIS BLOCK
    "spacing": "String (e.g., 'p-4 gap-4')",
    "radius": "String (e.g., 'rounded-lg')",
    "shadows": "String",
    "animations": "String"
  },

  "layout_plan": {
    "structure": "Description of the grid/layout",
    "sections": [
      {
        "name": "Section Name",
        "purpose": "What this does",
        "components": ["List", "Of", "Key", "Elements"]
      }
    ]
  },
  "component_patterns": {
    "card_style": "Description of how cards should look (shadows, borders)",
    "input_style": "Description of form inputs (if applicable)"
  },
  "ui_generation_prompt": "A highly detailed, step-by-step instruction string..."
}
"""

UI_GENERATOR_SYSTEM_PROMPT = """You are an expert React/Tailwind developer.
Your job is to convert a `design_plan` into a VALID JSON UI SCHEMA.

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

Allowed Types:
Root, Section, Container, Card, CardHeader, CardTitle, CardContent,
Form, Label, Input, Button, Text, Link, Icon, Image, Div

-------------------------------------------
CRITICAL VISUAL PATTERNS (DO NOT IGNORE)
-------------------------------------------

1. ICONS:
   Use the 'Icon' type. 
   {"type": "Icon", "props": {"name": "Mail", "className": "w-5 h-5 text-gray-400"}}
   (Valid names: Mail, Lock, User, Github, ArrowRight, LayoutDashboard, etc.)

2. FORM INPUTS:
   ALWAYS wrap inputs with a Label.
   Structure:
   {
     "type": "Div", "props": {"className": "space-y-2"},
     "children": [
        {"type": "Label", "content": "Email Address"},
        {"type": "Input", "props": {"className": "w-full border rounded-md p-2..."}}
     ]
   }

3. CARDS:
   Follow the Shadcn pattern:
   Card -> CardHeader (optional) -> CardContent -> CardFooter (optional).
   Add 'shadow-sm', 'border', 'bg-white', 'rounded-xl' to the main Card props.

4. LAYOUT:
   - For Login/Auth: Use a centered Flex or Grid layout (min-h-screen flex items-center justify-center).
   - For Dashboards: Use a Sidebar + Main Content layout.

-------------------------------------------
EXECUTION
-------------------------------------------
Read the `design_plan` provided by the user carefully. 
Apply the colors, typography, and layout strategies defined there.
Ensure the final JSON is valid and nest components correctly.
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
        ui_prompt = design_plan["ui_generation_prompt"]
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

        # Inject design context safely
        enhanced_prompt = f"""DESIGN SPECIFICATIONS:

THEME: {theme.get('style', 'modern')}
PRIMARY COLOR: {colors.get('primary', '#000000')}
BACKGROUND: {colors.get('background', '#ffffff')}
TYPOGRAPHY SCALE: Hero: {typography.get('heading', 'text-2xl font-bold')}, Body: {typography.get('body', 'text-sm')}

SPACING SYSTEM: {spacing}
BORDER RADIUS: {radius}

BUILD INSTRUCTIONS:
{prompt}

Remember: Use EXACT Tailwind classes. Build nested structures (Root → Section → Grid → Components). Create Text components with children for multi-colored text."""
        
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