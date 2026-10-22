import json
import logging
import time
import requests
from typing import Optional, Dict, Any
from django.conf import settings

# Import from existing llm.py
from .llm import GROQ_API_KEY, GROQ_URL, GEMINI_API_KEY, GEMINI_BASE_URL, _json_body
from .errors import LLMError, LLMInvalidResponseError, error_from_response, gemini_text, groq_text, provider_call
from .llm_models import DEFAULT_UI_MODEL, parse_model_id

logger = logging.getLogger(__name__)


class LLMChat:
    """Handle conversational UI refinement"""

    def __init__(self, ui_model_id: str = None):
        """
        Initialize chat client for UI refinements

        Args:
            ui_model_id: Composite "provider:model" id (e.g.
                "groq:openai/gpt-oss-20b"). Defaults to settings.DEFAULT_UI_MODEL.
        """
        self.ui_model_id = ui_model_id if ui_model_id else DEFAULT_UI_MODEL
        self.provider, self.ui_model = parse_model_id(self.ui_model_id)
        self.timeout = 60

        logger.info(f"LLMChat initialized with model: {self.ui_model_id}")
    
    def refine_ui(self, current_schema: dict, user_request: str, conversation_history: list = None) -> dict:
        """
        Refine existing UI based on user request
        
        Args:
            current_schema: Current UI schema dict
            user_request: User's refinement request
            conversation_history: List of previous {'role': str, 'content': str} messages
        
        Returns:
            dict with 'schema', 'ai_response', 'usage'
        """
        conversation_history = conversation_history or []
        
        # Build context from recent messages (last 5)
        context_messages = conversation_history[-5:] if conversation_history else []
        context_str = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in context_messages
        ])
        
        system_prompt = """You are a UI refinement assistant.
You receive an existing UI schema (JSON) and a user request to modify it.
Make ONLY the requested changes while preserving the overall structure and design.

Your response must be valid JSON with this exact structure:
{
  "schema": { ...updated schema... },
  "ai_response": "Brief 200-char explanation of changes made",
  "title": "Updated page title if changed"
}

RULES:
1. Only modify what the user asked for
2. Keep the same component types and structure
3. Maintain theme and styling consistency
4. Update content, layout, or styles as requested
5. ai_response should be concise (max 200 chars)
"""
        
        refinement_prompt = f"""Current UI Schema:
```json
{json.dumps(current_schema, indent=2)}
```

{f"Conversation Context:\n{context_str}\n" if context_str else ""}
User Request: {user_request}

Please update the schema based on the user's request and provide a brief explanation."""
        
        try:
            # Call the appropriate API based on provider
            if self.provider == "gemini":
                result = self._call_gemini(refinement_prompt, system_prompt, self.ui_model)
            else:
                result = self._call_groq_api(refinement_prompt, system_prompt, self.ui_model)
            
            # Validate response structure
            if not isinstance(result.get('schema'), dict):
                logger.error("Refinement response missing 'schema' object")
                raise LLMInvalidResponseError()
            
            # Ensure ai_response is max 200 chars
            ai_response = result.get('ai_response', 'UI updated based on your request')[:200]
            
            return {
                'schema': result['schema'],
                'ai_response': ai_response,
                'title': result.get('title', ''),
                'usage': result.get('usage', {})
            }
            
        except LLMError:
            raise  # typed, user-safe; the raw provider payload was logged already
        except Exception as e:
            logger.exception(f"UI refinement failed unexpectedly: {e}")
            raise LLMInvalidResponseError() from None
    
    def _call_groq_api(self, prompt: str, system_prompt: str, model: str) -> dict:
        """Call Groq API for refinement"""
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
            "temperature": 0.3,  # Lower temp for precise modifications
            "max_tokens": 8192,
        }
        
        with provider_call("groq"):
            response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                raise error_from_response("groq", response)
            data = _json_body("groq", response)

        return self._parse_response(groq_text(data), data.get("usage", {}))
    
    def _call_gemini(self, prompt: str, system_prompt: str, model: str) -> dict:
        """Call Gemini API for refinement"""
        # Key in a header, not the URL: URLs end up in exception text and logs.
        headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY or ""}

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
                "temperature": 0.3,
                "maxOutputTokens": 8192,
            }
        }

        url = f"{GEMINI_BASE_URL}/{model}:generateContent"
        with provider_call("gemini"):
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                raise error_from_response("gemini", response)
            data = _json_body("gemini", response)

        return self._parse_response(gemini_text(data), data.get("usageMetadata", {}))
    
    def _parse_response(self, content: str, usage: dict) -> dict:
        """Parse and validate JSON response"""
        # Remove markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        content = content.strip()
        
        # Remove control characters
        import re
        content = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', content)
        
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error: {e}")
            logger.error(f"Content preview: {content[:500]}")
            raise LLMInvalidResponseError() from None
        if not isinstance(parsed, dict):
            raise LLMInvalidResponseError()
        parsed["usage"] = usage
        return parsed
