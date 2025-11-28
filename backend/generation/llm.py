import json
import logging
import time
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GROQ_API_KEY = settings.GROQ_AI_API_KEY
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """
You are a UI generator that outputs Tailwind-based component schemas.

Return ONLY valid JSON in this structure:

{
  "title": "Readable UI title",
  "schema": {
    "type": "ComponentType",
    "class": "tailwind classes",
    "props": { ...optional non-style props... },
    "content": "text for Text or Button",
    "children": [ ...child components... ]
  }
}

STRICT RULES:
- ABSOLUTELY NO markdown or explanation.
- MUST be valid JSON parseable by json.loads.
- Styling MUST use Tailwind utility classes only.
- DO NOT use inline CSS. DO NOT output "width", "height", "backgroundColor", "border", or any raw style values.
- Allowed components: Container, Text, Button, Input, Grid, Card, Image.
- For Text → use "content" instead of children.
- For Button → use "content" for its label.
- For Input → "props" may contain only { "placeholder": "..." }.
- For Grid → "props" may contain { "cols": number }.
- "children" must be an array (may be empty).
- Keep classes minimal but meaningful: p-4, rounded-lg, bg-white, text-xl, grid-cols-3, flex, items-center, justify-center.
"""



def call_groq_once(prompt: str):
    """Single Groq call — low-level."""
    
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
        "temperature": 0.2,
    }

    logger.info("Calling Groq LLM with model llama-3.3-70b-versatile")

    resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=15)

    if resp.status_code != 200:
        logger.error("Groq Error: %s", resp.text)
        raise ValueError("Groq API Error: " + resp.text)

    json_msg = resp.json()

    content = json_msg["choices"][0]["message"]["content"]
    usage = json_msg.get("usage", {})

    return {
        "content": content,
        "usage": usage,
    }


def call_groq_model(prompt: str, retries: int = 2):
    """
    Adapter-style LLM call with retry, logging, and parsing.
    """

    for attempt in range(retries + 1):
        try:
            raw = call_groq_once(prompt)
            content = raw["content"]
            usage = raw["usage"]

            parsed = json.loads(content)

            return {
                "title": parsed.get("title"),
                "schema": parsed.get("schema"),
                "meta": {
                    "model": "llama-3.3-70b-versatile",
                    "usage": usage,
                },
            }

        except Exception as e:
            logger.error(f"LLM call failed attempt {attempt+1}: {e}")
            if attempt == retries:
                raise
            time.sleep(1.2)  # backoff
