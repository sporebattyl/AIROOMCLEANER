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

from backend.core.config import get_settings
from backend.core.exceptions import AIError, ConfigError


# Define constraints for image processing to prevent issues with large uploads.
MAX_IMAGE_SIZE_MB = 1  # Max image file size in megabytes.
MAX_IMAGE_DIMENSION = 2048  # Max width or height for an image.

# Global flag to ensure the Gemini client is configured only once.


class AIService:
    def __init__(self):
        self.gemini_client = None
        self.openai_client = None
        self._initialize_clients()

    def _initialize_clients(self):
        settings = get_settings()
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

    async def health_check(self) -> dict:
        """Performs a health check on the configured AI service."""
        settings = get_settings()
        model_lower = settings.ai_model.lower()
        if "gemini" in model_lower or "google" in model_lower:
            if not self.gemini_client or not genai:
                return {"status": "unconfigured", "error": "Gemini client not initialized or library not found."}
            try:
                # Simple check: list the first model to verify connection and API key.
                list(genai.list_models())
                return {"status": "ok", "provider": "google"}
            except Exception as e:
                logger.error(f"Gemini health check failed: {e}")
                return {"status": "error", "provider": "google", "error": str(e)}
        elif "gpt" in model_lower or "openai" in model_lower:
            if not self.openai_client or not openai:
                return {"status": "unconfigured", "error": "OpenAI client not initialized or library not found."}
            try:
                self.openai_client.models.list()
                return {"status": "ok", "provider": "openai"}
            except Exception as e:
                logger.error(f"OpenAI health check failed: {e}")
                return {"status": "error", "provider": "openai", "error": str(e)}
        else:
            return {"status": "error", "error": "No supported AI model configured for health check."}

    def analyze_room_for_mess(self, image_base64: str) -> List[dict]:
        settings = get_settings()
        logger.info(f"Using AI model: {settings.ai_model}")
        try:
            image_bytes = base64.b64decode(image_base64)
            with Image.open(io.BytesIO(image_bytes)) as img:
                optimized_img = self._optimize_image(img)
                sanitized_prompt = self._sanitize_prompt(settings.ai_prompt)
                model_lower = settings.ai_model.lower()

                if "gemini" in model_lower or "google" in model_lower:
                    return self._analyze_with_gemini(optimized_img, sanitized_prompt)
                elif "gpt" in model_lower or "openai" in model_lower:
                    return self._analyze_with_openai(optimized_img, sanitized_prompt)
                else:
                    raise AIError(f"Unsupported or unrecognized AI model: {settings.ai_model}")
        except Exception as e:
            logger.error(f"Failed to decode or process image: {e}", exc_info=True)
            raise AIError("Invalid image format or processing error.")

    def _analyze_with_gemini(self, image: Image.Image, prompt: str) -> List[dict]:
        if not self.gemini_client:
            raise ConfigError("Gemini client not initialized.")
        try:
            response = self.gemini_client.generate_content([prompt, image])
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

    def _analyze_with_openai(self, image: Image.Image, prompt: str) -> List[dict]:
        if not self.openai_client:
            raise ConfigError("OpenAI client not initialized.")
        try:
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            response = self.openai_client.chat.completions.create(
                model=get_settings().ai_model,
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

    def _optimize_image(self, img: Image.Image) -> Image.Image:
        # Check size based on a rough estimation of bytes per pixel
        # This is not perfect but avoids saving to buffer just for a size check.
        estimated_size = img.width * img.height * 4  # RGBA
        if estimated_size > MAX_IMAGE_SIZE_MB * 1024 * 1024 or \
           img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            logger.info("Image is large, resizing...")
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
        return img

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