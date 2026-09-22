import json
import asyncio
import logging
import re
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
import openai

from app.core.config import settings

logger = logging.getLogger(__name__)

# List of models ordered by fallback preference. Removed slow ones to speed up generation.
FREE_MODELS = [
    "nvidia/nemotron-3.5-lightning:free",
    "google/gemini-1.5-flash:free",
    "meta-llama/llama-3.1-8b-instruct:free",
]

class OpenRouterClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
            timeout=8.0,
        )

    async def generate_content(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """
        Attempts to generate content with fallback logic.
        Cycles through models if rate limited or if the request fails due to credits.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_error = None

        for model_name in FREE_MODELS:
            try:
                print(f"Trying OpenRouter model: {model_name}")
                response = await self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                )
                if response.choices and len(response.choices) > 0:
                    text = response.choices[0].message.content
                    if text is not None:
                        return text
            except openai.RateLimitError as e:
                print(f"RateLimitError on {model_name}: {e}")
                last_error = e
                continue
            except openai.AuthenticationError as e:
                print(f"AuthError on {model_name}: {e}")
                last_error = e
                continue
            except openai.APITimeoutError as e:
                print(f"APITimeoutError on {model_name}: {e}")
                last_error = e
                continue
            except openai.APIStatusError as e:
                # 402 is insufficient credits in some cases
                if e.status_code in [402, 429, 502, 503, 504, 520, 521, 522]:
                    print(f"Status Error {e.status_code} on {model_name}: {e}")
                    last_error = e
                    continue
                else:
                    print(f"APIStatusError {e.status_code} on {model_name}: {e}")
                    last_error = e
                    continue
            except Exception as e:
                print(f"Unexpected error on {model_name}: {e}")
                last_error = e
                continue

        raise RuntimeError(f"All OpenRouter free models failed. Last error: {str(last_error)}")

    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """Bulletproof JSON extraction from markdown blocks or raw text."""
        text = text.strip()
        # Find json block using regex
        match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
        
        # If it doesn't match, maybe it's just raw json.
        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end+1]
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}\nText was: {text}")
