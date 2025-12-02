import json
import logging
import time
import requests
from typing import Optional, Dict, Any
from django.conf import settings
from functools import wraps

logger = logging.getLogger(__name__)

GROQ_API_KEY = settings.GROQ_AI_API_KEY
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_API_KEY = settings.GEMINI_API_KEY
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Advanced system prompt that produces production-grade UIs
SYSTEM_PROMPT = """You are an elite UI/UX developer AI that generates modern, accessible React components using Tailwind CSS and shadcn/ui patterns.

OUTPUT FORMAT: Return ONLY valid JSON (no markdown, no explanations):

{
  "title": "Project Title",
  "schema": {
    "type": "Root",
    "props": {
      "className": "tailwind classes",
      "id": "unique-id"
    },
    "children": [...]
  },
  "code": "/* Complete, runnable React component code goes here */",
  "metadata": {
    "framework": "react",
    "tailwindVersion": "3.4",
    "shadcnComponents": ["button", "card", "input", "separator", "badge"],
    "accessibility": "wcag2.1-aa"
  }
}

COMPONENT TYPES:
- Root: Wrapper component (typically flex/grid container)
- Section: Semantic section with padding and spacing
- Card: shadcn-style card with shadow and border
- Grid: Responsive grid layout
- Flex: Flexbox container
- **Form:** Wrapper for form controls
- **Label:** Accessible label for form fields
- **Text:** Paragraph/heading/span element (requires a 'tag' prop)
- **Link/A:** Anchor tag for navigation
- Button: Interactive button
- Input: Form field
- Textarea: Multi-line text
- Select: Dropdown select
- Image: Responsive image (requires 'alt' prop)
- **List:** Semantic list wrapper (ul or ol)
- **ListItem:** Semantic list item wrapper (li)
- Badge: Tag/label component
- Skeleton: Loading placeholder
- Separator: Divider

MANDATORY RULES:
1. ALWAYS use semantic HTML (article, section, nav, main, aside)
2. ONLY Tailwind classes in className (no inline styles)
3. Include proper spacing: p-4, p-6, gap-4, space-y-4
4. Mobile-first responsive: sm:, md:, lg:, xl: prefixes
5. **Accessibility: Include `aria-labels`, `role` attributes, and `alt` text for images. Ensure keyboard navigability (tabindex/focus states).**
6. Colors: Use neutral-950, neutral-50, blue-600, emerald-500 etc. (Tailwind palette)
7. For every interactive element, add hover/focus states
8. Typography: Use font-semibold, text-lg, leading-relaxed etc.
9. **Include proper icons (use lucide-react icon names in the component's `props` field, e.g., `props: { icon: "Heart" }`).**
10. Never use absolute positioning unless absolutely necessary
11. **All components derived from base HTML must specify their semantic tag in a 'tag' prop (e.g., `Text` must include `props: { tag: "h2" }`).**

DESIGN PRINCIPLES:
- Modern minimalist aesthetic (Apple, Vercel, Anthropic style)
- Proper visual hierarchy with spacing and typography
- **Clear use of whitespace for grouping related content (Gestalt Principles).**
- Consistent color scheme (limit to 3-4 colors)
- Accessible color contrast ratios
- Smooth animations (transition, transform)
- Professional gradients where appropriate
- **Micro-interactions: Use `hover:scale-[1.01]`, `hover:shadow-xl` on interactive cards/links.**

COMPONENT STRUCTURE:
Each component must have:
- type: string (from list above)
- props: { className: "...", id?: "...", **tag?: "h1"|"p"|"ul" etc.**, **icon?: "lucide-icon-name"**, **alt?: "..."** }
- children: array of child components OR content string

SEMANTIC TEXT EXAMPLE:
{
  "type": "Text",
  "props": { "tag": "h2", "className": "text-2xl font-bold text-neutral-900 mb-4" },
  "content": "Our Services"
}

MODERN LINK EXAMPLE WITH ICON:
{
  "type": "Link/A",
  "props": {
    "href": "/appointments",
    "icon": "Calendar",
    "className": "flex items-center gap-2 text-blue-600 hover:text-blue-800 transition-colors"
  },
  "children": [{ "type": "Text", "content": "Book Now" }]
}

Now generate a modern, professional UI based on the user's request. Think deeply about layout, spacing, colors, and user experience. Ensure the output is a complete JSON object including both the `schema` and the `code` fields.
"""


class LLMClient:
    """Abstracted LLM client supporting Groq and Gemini with retry logic"""
    
    def __init__(self, provider: str = "groq"):
        self.provider = provider.lower()
        self.timeout = 30
        
    def call(self, prompt: str, retries: int = 3) -> Dict[str, Any]:
        """Main entry point with retry and error handling"""
        for attempt in range(retries):
            try:
                if self.provider == "groq":
                    return self._call_groq(prompt)
                elif self.provider == "gemini":
                    return self._call_gemini(prompt)
                else:
                    raise ValueError(f"Unknown provider: {self.provider}")
            except Exception as e:
                logger.error(f"LLM attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # exponential backoff
                else:
                    raise
    
    def _call_groq(self, prompt: str) -> Dict[str, Any]:
        """Call Groq API"""
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }
        
        logger.info("Calling Groq LLM")
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=self.timeout)
        
        if response.status_code != 200:
            raise ValueError(f"Groq API Error: {response.text}")
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        
        return self._parse_response(content, usage, "groq")
    
    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini API"""
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": SYSTEM_PROMPT},
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 4096,
            }
        }
        
        url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        logger.info("Calling Gemini API")
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        
        if response.status_code != 200:
            raise ValueError(f"Gemini API Error: {response.text}")
        
        data = response.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        
        return self._parse_response(content, usage, "gemini")
    
    def _parse_response(self, content: str, usage: Dict, provider: str) -> Dict[str, Any]:
        """Extract and validate JSON from LLM response"""
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        content = content.strip()
        
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {provider}: {e}")
            raise ValueError(f"Invalid JSON from LLM: {str(e)}")
        
        return {
            "title": parsed.get("title", "Generated UI"),
            "schema": parsed.get("schema", {}),
            "metadata": parsed.get("metadata", {}),
            "usage": usage,
            "provider": provider,
        }

