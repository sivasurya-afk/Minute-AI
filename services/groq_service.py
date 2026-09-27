"""
Groq API client wrapper with retry handling, structured JSON mode, and model management.
"""

from typing import Dict, Any, Optional
import os
import time
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Default model constants
DEFAULT_LLM_MODEL = "qwen/qwen3.8-27b"
DEFAULT_TRANSCRIPTION_MODEL = "whisper-large-v3"
AVAILABLE_GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "mixtral-8x7b-32768",
]


class GroqService:
    """Service to interact with the Groq Cloud API."""

    _instance: Optional["GroqService"] = None

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.client = None

        if self.api_key and not self.api_key.startswith("your_"):
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize Groq client: {e}")

    @classmethod
    def get_instance(cls) -> "GroqService":
        if cls._instance is None:
            cls._instance = GroqService()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def is_configured(self) -> bool:
        """Check if a valid Groq API key is configured."""
        return self.client is not None and bool(self.api_key) and not self.api_key.startswith("your_")

    def chat_completion_json(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Execute Groq chat completion demanding valid JSON response with retry backoff.
        """
        if not self.is_configured():
            raise ValueError(
                "Groq API Key is not configured. Please set GROQ_API_KEY in .env or Settings."
            )

        chosen_model = model or os.getenv("GROQ_LLM_MODEL", DEFAULT_LLM_MODEL)
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=chosen_model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                raw_content = response.choices[0].message.content
                if not raw_content:
                    raise ValueError("Groq returned an empty response.")
                parsed_json = json.loads(raw_content)
                return parsed_json
            except json.JSONDecodeError as jde:
                last_error = f"JSON decode error: {jde}"
                logger.warning(f"Attempt {attempt + 1}: Malformed JSON from Groq: {jde}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1}: Groq API call failed: {e}")
                # Exponential backoff on rate limits or network issues
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        raise RuntimeError(f"Groq API completion failed after {max_retries} attempts. Last error: {last_error}")
