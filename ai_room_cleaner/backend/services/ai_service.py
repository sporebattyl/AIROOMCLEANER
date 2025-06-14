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

import bleach

# Optional dependency imports for AI providers.
from backend.utils.image_processing import resize_image_with_vips, configure_pyvips
# These are wrapped in try-except blocks to allow the application to run
# even if only one provider's libraries are installed.
try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    genai = None
    GOOGLE_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

from backend.core.config import get_settings
from backend.core.exceptions import AIError, ConfigError, ImageProcessingError



# Global flag to ensure the Gemini client is configured only once.


class AIService:
    def __init__(self, settings):
        self.settings = settings
        self.gemini_client = None
        self.openai_client = None
        self.MAX_IMAGE_SIZE_MB = settings.max_image_size_mb
        self.MAX_IMAGE_DIMENSION = settings.max_image_dimension
        self._initialize_clients()
        configure_pyvips(self.settings)

    def _initialize_clients(self):
        if not self.settings.ai_model:
            raise ConfigError("AI model not specified in configuration.")

        model_lower = self.settings.ai_model.lower()
        if "gemini" in model_lower or "google" in model_lower:
            if not genai:
                raise ConfigError("Google AI libraries not installed. Please run: pip install google-generativeai pillow")
            if not self.settings.google_api_key:
                raise ConfigError("Google API key is not configured for the selected Gemini model.")
            genai.configure(api_key=self.settings.google_api_key.get_secret_value())
            self.gemini_client = genai.GenerativeModel(self.settings.ai_model)
        elif "gpt" in model_lower or "openai" in model_lower:
            if not openai:
                raise ConfigError("OpenAI library not installed. Please run: pip install openai")
            if not self.settings.openai_api_key:
                raise ConfigError("OpenAI API key is not configured for the selected GPT model.")
            self.openai_client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key.get_secret_value())
        else:
            raise AIError(f"Unsupported or unrecognized AI model: {self.settings.ai_model}")

    async def health_check(self) -> dict:
        """Performs a health check on the configured AI service."""
        model_lower = self.settings.ai_model.lower()
        if "gemini" in model_lower or "google" in model_lower:
            if not self.gemini_client or not genai:
                return {"status": "unconfigured", "error": "Gemini client not initialized or library not found."}
            try:
                list(genai.list_models())
                return {"status": "ok", "provider": "google"}
            except Exception as e:
                logger.error(f"Gemini health check failed: {e}")
                return {"status": "error", "provider": "google", "error": str(e)}
        elif "gpt" in model_lower or "openai" in model_lower:
            if not self.openai_client or not openai:
                return {"status": "unconfigured", "error": "OpenAI client not initialized or library not found."}
            try:
                await self.openai_client.models.list()
                return {"status": "ok", "provider": "openai"}
            except Exception as e:
                logger.error(f"OpenAI health check failed: {e}")
                return {"status": "error", "provider": "openai", "error": str(e)}
        else:
            return {"status": "error", "error": "No supported AI model configured for health check."}

    async def analyze_room_for_mess(self, image_base64: str) -> List[dict]:
        logger.info(f"Using AI model: {self.settings.ai_model}")
        
        # Validate input
        if not image_base64 or not isinstance(image_base64, str):
            raise AIError("Invalid or empty image data provided.")
        
        try:
            # Validate base64 format
            try:
                image_bytes = base64.b64decode(image_base64, validate=True)
            except Exception as e:
                raise AIError(f"Invalid base64 image data: {str(e)}")
            
            # Validate image size
            if len(image_bytes) == 0:
                raise AIError("Decoded image data is empty.")
            
            if len(image_bytes) > self.MAX_IMAGE_SIZE_MB * 1024 * 1024:
                raise AIError(f"Image size ({len(image_bytes)} bytes) exceeds maximum allowed size ({self.MAX_IMAGE_SIZE_MB}MB).")
            
            # Process image with better error handling
            try:
                resized_image_bytes = resize_image_with_vips(image_bytes, self.settings)
            except Exception as e:
                logger.error(f"Image processing failed: {e}", exc_info=True)
                raise ImageProcessingError(f"Failed to process image: {str(e)}")
            
            sanitized_prompt = self._sanitize_prompt(self.settings.ai_prompt)
            model_lower = self.settings.ai_model.lower()
    
            if "gemini" in model_lower or "google" in model_lower:
                return await self._analyze_with_gemini(resized_image_bytes, sanitized_prompt)
            elif "gpt" in model_lower or "openai" in model_lower:
                return await self._analyze_with_openai(resized_image_bytes, sanitized_prompt)
            else:
                raise AIError(f"Unsupported or unrecognized AI model: {self.settings.ai_model}")
                
        except (AIError, ImageProcessingError, ConfigError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error in room analysis: {e}", exc_info=True)
            raise AIError(f"Unexpected error during analysis: {str(e)}")

    async def _analyze_with_gemini(self, image_bytes: bytes, prompt: str) -> List[dict]:
        if not self.gemini_client:
            raise ConfigError("Gemini client not initialized.")
        try:
            # The gemini client can accept image bytes directly
            image_parts = [{"mime_type": "image/jpeg", "data": image_bytes}]
            response = await self.gemini_client.generate_content_async([prompt, image_parts])
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

    async def _analyze_with_openai(self, image_bytes: bytes, prompt: str) -> List[dict]:
        if not self.openai_client:
            raise ConfigError("OpenAI client not initialized.")
        try:
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            response = await self.openai_client.chat.completions.create(
                model=self.settings.ai_model,
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

    # The _optimize_image function is no longer needed as resizing is now handled by the vips utility.

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