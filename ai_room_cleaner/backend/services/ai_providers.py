"""
This module defines the abstraction for AI providers using the Strategy pattern.

It includes:
- An abstract base class `AIProvider` that defines the common interface for all AI providers.
- Concrete implementations of `AIProvider` for various services (e.g., OpenAI, Google Gemini).
- A factory function `get_ai_provider` to instantiate the correct provider based on configuration.
"""
import base64
from abc import ABC, abstractmethod
import json
import re
from typing import List, Dict, Any
from loguru import logger
import openai
from google.generativeai.client import configure  # pylint: disable=no-name-in-module
from google.generativeai.generative_models import GenerativeModel  # pylint: disable=no-name-in-module
from google.api_core import exceptions as google_exceptions


from ..core.config import AppSettings
from ..core.exceptions import (
    AIError,
    ConfigError,
    InvalidAPIKeyError,
    APIResponseError,
    AIProviderError,
)

class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, settings: AppSettings):
        self.settings = settings

    @abstractmethod
    async def analyze_image(
        self, image_data: bytes, prompt: str, mime_type: str = "image/jpeg"
    ) -> List[Dict[str, Any]]:
        """Analyzes an image and returns a list of tasks."""

    @abstractmethod
    async def health_check(self) -> dict:
        """Performs a live health check against the provider's API."""

    def _parse_ai_response(self, text_content: str) -> List[Dict[str, Any]]:
        logger.debug(f"Attempting to parse AI response: {text_content}")
        try:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text_content)
            if match:
                text_content = match.group(1)
            data = json.loads(text_content.strip())
            if isinstance(data, dict) and "tasks" in data:
                tasks = data["tasks"]
                if isinstance(tasks, list):
                    logger.info(f"Successfully parsed {len(tasks)} tasks.")
                    return tasks

            if isinstance(data, list):
                logger.warning(
                    "AI returned a list instead of a dict. Converting to new format."
                )
                return [{"mess": str(item), "reason": "N/A"} for item in data]

            logger.error("AI response is not in the expected format.")
            return []
        except json.JSONDecodeError:
            logger.warning(
                "Failed to decode JSON from AI response. "
                "Falling back to text-based parsing."
            )
            return self._parse_text_response(text_content)

    def _parse_text_response(self, text: str) -> List[Dict[str, Any]]:
        logger.warning("Falling back to text-based parsing for AI response.")
        tasks = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if (
                not line
                or line.startswith("#")
                or line.startswith("{")
                or line in ["```", "```json", "tasks:"]
            ):
                continue
            line = line.lstrip('•-*[]"').rstrip('",').strip()
            if line and len(line) > 10:
                tasks.append({"mess": line, "reason": "Parsed from text"})
        if not tasks:
            logger.warning("Could not extract any tasks from text response.")
            return []
        logger.info(f"Extracted {len(tasks)} tasks using fallback text parser.")
        return tasks[:10]

class OpenAIProvider(AIProvider):
    """AI Provider implementation for OpenAI's GPT models."""

    def __init__(self, settings: AppSettings):
        super().__init__(settings)
        if not self.settings.ai_api_key:
            raise ConfigError("OpenAI API key is not configured.")
        self.client = openai.AsyncOpenAI(api_key=self.settings.ai_api_key.get_secret_value())

    async def analyze_image(
        self, image_data: bytes, prompt: str, mime_type: str = "image/jpeg"
    ) -> List[Dict[str, Any]]:
        if not self.client:
            raise ConfigError("OpenAI client not initialized.")
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.AI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=self.settings.OPENAI_MAX_TOKENS,
            )
            text_content = response.choices[0].message.content
            if not text_content:
                raise APIResponseError("OpenAI returned an empty response.")
            logger.info(f"Raw OpenAI response: {text_content}")
            return self._parse_ai_response(text_content)
        except openai.APIStatusError as e:
            if e.status_code == 401:
                raise InvalidAPIKeyError("OpenAI API key is invalid.") from e
            raise AIProviderError(f"OpenAI API error: {e}") from e
        except Exception as e:
            raise AIProviderError("An unexpected error occurred with OpenAI.") from e

    async def health_check(self) -> dict:
        """Performs a live health check against the OpenAI API."""
        try:
            await self.client.models.list()
            logger.info("OpenAI health check successful.")
            return {"status": "ok", "provider": "OpenAI"}
        except openai.APIStatusError as e:
            if e.status_code == 401:
                raise InvalidAPIKeyError("OpenAI API key is invalid.") from e
            raise AIProviderError(f"OpenAI API error: {e}") from e
        except openai.APIError as e:
            logger.error(f"Error with OpenAI analysis: {e}", exc_info=True)
            raise AIProviderError("Failed to analyze image with OpenAI.") from e

class GoogleGeminiProvider(AIProvider):
    """AI Provider implementation for Google's Gemini models."""

    def __init__(self, settings: AppSettings):
        super().__init__(settings)
        if not self.settings.ai_api_key:
            raise ConfigError("Google API key is not configured.")
        configure(api_key=self.settings.ai_api_key.get_secret_value())
        self.client = GenerativeModel(self.settings.AI_MODEL)

    async def analyze_image(
        self, image_data: bytes, prompt: str, mime_type: str = "image/jpeg"
    ) -> List[Dict[str, Any]]:
        if not self.client:
            raise ConfigError("Gemini client not initialized.")
        try:
            image_parts = {"mime_type": mime_type, "data": image_data}
            response = await self.client.generate_content_async([prompt, image_parts])
            if not response.parts:
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    reason = (
                        "Content blocked by Gemini. "
                        f"Reason: {response.prompt_feedback.block_reason}"
                    )
                    logger.warning(reason)
                    return [
                        {"description": reason, "reason": "Blocked by AI safety filter"}
                    ]
                logger.warning("Gemini returned an empty but valid response.")
                return [
                    {
                        "description": "The AI returned an empty response, "
                        "indicating no mess was found.",
                        "reason": "Empty response",
                    }
                ]

            text_content = "".join(
                part.text for part in response.parts if hasattr(part, "text")
            )
            if not text_content:
                raise AIError("Gemini returned a response with no text content.")
            logger.info(f"Raw Gemini response: {text_content}")
            return self._parse_ai_response(text_content)
        except (google_exceptions.PermissionDenied, google_exceptions.Unauthenticated) as e:
            logger.error(f"Google API authentication error: {e}", exc_info=True)
            raise InvalidAPIKeyError(
                "Google API key is invalid or has insufficient permissions."
            ) from e
        except google_exceptions.GoogleAPICallError as e:
            raise AIProviderError(f"Google API error: {e}") from e

    async def health_check(self) -> dict:
        """Performs a live health check against the Google Gemini API."""
        try:
            # A lightweight, low-cost call to verify connectivity
            self.client.count_tokens("hello")
            logger.info("Google Gemini health check successful.")
            return {"status": "ok", "provider": "Google"}
        except google_exceptions.GoogleAPICallError as e:
            logger.error(f"Google Gemini health check failed: {e}")
            return {"status": "error", "provider": "Google", "details": str(e)}

def get_ai_provider(provider_name: str, settings: AppSettings) -> AIProvider:
    """Factory function to get an AI provider instance."""
    provider_name = provider_name.lower()
    if provider_name == "openai":
        return OpenAIProvider(settings)
    if provider_name == "google":
        return GoogleGeminiProvider(settings)
    raise ConfigError(f"Unknown or unsupported AI provider: {provider_name}")
