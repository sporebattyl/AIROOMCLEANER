"""
This service is responsible for interacting with a generative AI model
to analyze images of a room and identify sources of mess. It supports
multiple AI providers (Google Gemini, OpenAI GPT) and handles image
preprocessing, prompt sanitization, and robust parsing of the AI's response.
"""
import asyncio
import base64
import tempfile
import shutil
from loguru import logger
from typing import List, Dict, Any
import bleach
from fastapi import UploadFile

from backend.core.config import Settings
from backend.core.exceptions import (
    AIError,
    ConfigError,
    ImageProcessingError,
    AIProviderError
)
from backend.utils.image_processing import resize_image_with_vips, configure_pyvips
from .ai_providers import get_ai_provider, AIProvider


class AIService:
    """
    Service for interacting with a generative AI model to analyze room images.
    Uses the Strategy and Factory patterns to support multiple AI providers.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        # The AI provider is determined by the settings
        self.ai_provider: AIProvider = get_ai_provider(settings.AI_PROVIDER, settings)
        # Configure the image processing library
        configure_pyvips(self.settings)
        logger.info(f"AIService initialized with provider: {settings.AI_PROVIDER}")

    async def health_check(self) -> Dict[str, Any]:
        """Performs a health check on the configured AI service."""
        # The health check logic is now delegated to the provider implementation.
        # For simplicity, we'll just check if the provider is initialized.
        # A more thorough health check would involve making a test call to the AI API.
        if self.ai_provider:
            return {"status": "ok", "provider": self.settings.AI_PROVIDER}
        else:
            return {"status": "error", "error": "AI provider not initialized."}

    async def analyze_room_for_mess(self, image_base64: str) -> List[Dict[str, Any]]:
        """
        Analyzes a room image for mess by delegating to the configured AI provider.
        """
        logger.info(f"Using AI provider: {self.settings.AI_PROVIDER}, model: {self.settings.AI_MODEL}")

        # Validate the input image data
        if not image_base64 or not isinstance(image_base64, str):
            raise AIError("Invalid or empty image data provided.")

        try:
            # Decode, validate, and process the image
            image_bytes = await self._decode_and_validate_image(image_base64)
            resized_image_bytes = self._process_image(image_bytes)
            # Sanitize the prompt to prevent injection attacks
            sanitized_prompt = self._sanitize_prompt(self.settings.AI_PROMPT)

            # Delegate the analysis to the configured AI provider
            return await self.ai_provider.analyze_image(resized_image_bytes, sanitized_prompt)

        except (
            AIError,
            ImageProcessingError,
            ConfigError,
            AIProviderError,
        ) as e:
            logger.error(f"A specific error occurred: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred in room analysis: {e}", exc_info=True)
            raise AIError(f"An unexpected error occurred during analysis: {str(e)}")

    async def analyze_image_from_upload(
        self, upload_file: UploadFile
    ) -> List[Dict[str, Any]]:
        """
        Analyzes an image from an UploadFile by streaming it to a temporary file.
        This avoids loading the entire file into memory.
        """
        temp_dir = tempfile.mkdtemp()
        temp_path = f"{temp_dir}/{upload_file.filename}"
        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(upload_file.file, buffer)

            with open(temp_path, "rb") as f:
                image_bytes = f.read()

            # Now that we have the bytes, we can proceed with existing logic
            resized_image_bytes = self._process_image(image_bytes)
            sanitized_prompt = self._sanitize_prompt(self.settings.AI_PROMPT)
            return await self.ai_provider.analyze_image(
                resized_image_bytes, sanitized_prompt
            )
        finally:
            shutil.rmtree(temp_dir)
            await upload_file.close()

    async def _decode_and_validate_image(self, image_base64: str) -> bytes:
        """Decodes, validates, and checks the size of the base64 image."""
        try:
            image_bytes = await asyncio.to_thread(base64.b64decode, image_base64, validate=True)
        except Exception as e:
            raise AIError(f"Invalid base64 image data: {str(e)}")

        if not image_bytes:
            raise AIError("Decoded image data is empty.")

        max_size = self.settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if len(image_bytes) > max_size:
            raise AIError(f"Image size ({len(image_bytes)} bytes) exceeds maximum of {self.settings.MAX_IMAGE_SIZE_MB}MB.")
        
        return image_bytes

    def _process_image(self, image_bytes: bytes) -> bytes:
        """Resizes the image using the vips utility."""
        try:
            return resize_image_with_vips(image_bytes, self.settings)
        except Exception as e:
            logger.error(f"Image processing failed: {e}", exc_info=True)
            raise ImageProcessingError(f"Failed to process image: {str(e)}")

    def _sanitize_prompt(self, prompt: str) -> str:
        """Sanitizes the prompt to remove any potentially harmful content."""
        return bleach.clean(prompt, tags=[], attributes={}, strip=True)