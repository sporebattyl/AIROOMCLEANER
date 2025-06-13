"""
This service is responsible for interacting with a generative AI model
to analyze images of a room and identify sources of mess. It supports
multiple AI providers (Google Gemini, OpenAI GPT) and handles image
preprocessing, prompt sanitization, and robust parsing of the AI's response.
"""
import base64
import io
import json
from loguru import logger
import re
from typing import List
from pydantic import SecretStr

import bleach
from PIL import Image

# Optional dependency imports for AI providers.
# These are wrapped in try-except blocks to allow the application to run
# even if only one provider's libraries are installed.
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None

from backend.core.config import settings
from backend.core.exceptions import AIError, ConfigError


# Define constraints for image processing to prevent issues with large uploads.
MAX_IMAGE_SIZE_MB = 1  # Max image file size in megabytes.
MAX_IMAGE_DIMENSION = 2048  # Max width or height for an image.

# Global flag to ensure the Gemini client is configured only once.
_gemini_configured = False


class AIService:
    def __init__(self):
        self.gemini_client = None
        self.openai_client = None
        self._initialize_clients()

    def _initialize_clients(self):
        if not settings.ai_model:
            raise ConfigError("AI model not specified in configuration.")

        model_lower = settings.ai_model.lower()
        if "gemini" in model_lower or "google" in model_lower:
            if not genai:
                raise ConfigError("Google AI libraries not installed. Please run: pip install google-generativeai pillow")
            api_key = settings.google_api_key
            if not api_key:
                raise ConfigError("Google API key is not configured for the selected Gemini model.")
            genai.configure(api_key=api_key.get_secret_value())
            self.gemini_client = genai.GenerativeModel(settings.ai_model)
        elif "gpt" in model_lower or "openai" in model_lower:
            if not openai:
                raise ConfigError("OpenAI library not installed. Please run: pip install openai")
            api_key = settings.openai_api_key
            if not api_key:
                raise ConfigError("OpenAI API key is not configured for the selected GPT model.")
            self.openai_client = openai.OpenAI(api_key=api_key.get_secret_value())
        else:
            raise AIError(f"Unsupported or unrecognized AI model: {settings.ai_model}")

    def analyze_room_for_mess(self, image_base64: str) -> List[dict]:
        logger.info(f"Using AI model: {settings.ai_model}")

        try:
            image_bytes = base64.b64decode(image_base64)
            optimized_image_bytes = self._optimize_image(image_bytes)
            optimized_image_base64 = base64.b64encode(optimized_image_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decode or optimize image: {e}", exc_info=True)
            raise AIError("Invalid image format or processing error.")

        sanitized_prompt = self._sanitize_prompt(settings.ai_prompt)
        model_lower = settings.ai_model.lower()

        if "gemini" in model_lower or "google" in model_lower:
            return self._analyze_with_gemini(optimized_image_base64, sanitized_prompt)
        elif "gpt" in model_lower or "openai" in model_lower:
            return self._analyze_with_openai(optimized_image_base64, sanitized_prompt)
        else:
            raise AIError(f"Unsupported or unrecognized AI model: {settings.ai_model}")

    def _analyze_with_gemini(self, image_base64: str, prompt: str) -> List[dict]:
        if not self.gemini_client:
            raise ConfigError("Gemini client not initialized.")
        try:
            image_bytes = base64.b64decode(image_base64)
            img = Image.open(io.BytesIO(image_bytes))
            response = self.gemini_client.generate_content([prompt, img])

            if not response.parts:
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    reason = f"Content blocked by Gemini. Reason: {response.prompt_feedback.block_reason}"
                    logger.warning(reason)
                    return [{"description": reason, "reason": "Blocked by AI safety filter"}]
                logger.warning("Gemini returned an empty but valid response.")
                return [{"description": "The AI returned an empty response, indicating no mess was found.", "reason": "Empty response"}]

            text_content = "".join(part.text for part in response.parts if hasattr(part, "text"))
            if not text_content:
                raise AIError("Gemini returned a response with no text content.")
            logger.info(f"Raw Gemini response: {text_content}")
            return self._parse_ai_response(text_content)
        except Exception as e:
            logger.error(f"Error with Gemini analysis: {e}", exc_info=True)
            raise AIError("Failed to analyze image with Gemini.") from e

    def _analyze_with_openai(self, image_base64: str, prompt: str) -> List[dict]:
        if not self.openai_client:
            raise ConfigError("OpenAI client not initialized.")
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                max_tokens=1000
            )
            text_content = response.choices[0].message.content
            if not text_content:
                raise AIError("OpenAI returned an empty response.")
            logger.info(f"Raw OpenAI response: {text_content}")
            return self._parse_ai_response(text_content)
        except Exception as e:
            logger.error(f"Error with OpenAI analysis: {e}", exc_info=True)
            raise AIError("Failed to analyze image with OpenAI.") from e

    def _sanitize_prompt(self, prompt: str) -> str:
        return bleach.clean(prompt, tags=[], attributes={}, strip=True)

    def _optimize_image(self, image_bytes: bytes) -> bytes:
        if len(image_bytes) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            logger.info(f"Image is larger than {MAX_IMAGE_SIZE_MB}MB, resizing...")
            img = Image.open(io.BytesIO(image_bytes))
            if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
                img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85, optimize=True)
            return buffer.getvalue()
        return image_bytes

    def _parse_ai_response(self, text_content: str) -> List[dict]:
        logger.debug(f"Attempting to parse AI response: {text_content}")
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text_content)
        if match:
            text_content = match.group(1)
        try:
            data = json.loads(text_content.strip())
            if isinstance(data, dict) and "tasks" in data:
                tasks = data["tasks"]
                if isinstance(tasks, list):
                    if all(isinstance(item, dict) for item in tasks):
                        logger.info(f"Successfully parsed {len(tasks)} tasks.")
                        return tasks
                    else:
                        logger.warning("Tasks in JSON are not formatted as objects. Attempting to convert.")
                        return [{"mess": str(item), "reason": "N/A"} for item in tasks]
                else:
                    raise AIError("AI response's 'tasks' key is not a list.")
            elif isinstance(data, list):
                logger.warning("AI returned a list instead of a dict. Converting to new format.")
                return [{"mess": str(item), "reason": "N/A"} for item in data]
            else:
                raise AIError("AI response is not a JSON object with a 'tasks' key.")
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from AI response.", exc_info=True)
            return self._parse_text_response(text_content)
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}", exc_info=True)
            raise AIError("Failed to parse the AI's response.")

    def _parse_text_response(self, text: str) -> List[dict]:
        logger.warning("Falling back to text-based parsing for AI response.")
        tasks = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('{') or line in ['```', '```json', 'tasks:']:
                continue
            line = line.lstrip('•-*[]"').rstrip('",').strip()
            if line and len(line) > 10:
                tasks.append({"mess": line, "reason": "Parsed from text"})
        if not tasks:
            logger.warning("Could not extract any tasks from text response.")
            return []
        logger.info(f"Extracted {len(tasks)} tasks using fallback text parser.")
        return tasks[:10]