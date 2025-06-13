"""
This service is responsible for interacting with a generative AI model
to analyze images of a room and identify sources of mess. It supports
multiple AI providers (Google Gemini, OpenAI GPT) and handles image
preprocessing, prompt sanitization, and robust parsing of the AI's response.
"""
import base64
import io
import json
import logging
import re
from typing import List

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

logger = logging.getLogger(__name__)

# Define constraints for image processing to prevent issues with large uploads.
MAX_IMAGE_SIZE_MB = 1  # Max image file size in megabytes.
MAX_IMAGE_DIMENSION = 2048  # Max width or height for an image.

# Global flag to ensure the Gemini client is configured only once.
_gemini_configured = False


def _sanitize_prompt(prompt: str) -> str:
    """
    Sanitizes the AI prompt to remove potentially harmful content like HTML/JS tags.
    
    Args:
        prompt: The raw prompt string.
        
    Returns:
        A sanitized string with all tags stripped out.
    """
    return bleach.clean(prompt, tags=[], attributes={}, strip=True)


def _optimize_image(image_bytes: bytes) -> bytes:
    """
    Resizes and re-compresses an image if it's too large, either by file size or dimensions.
    This helps reduce upload times and costs, and meets AI provider limits.

    Args:
        image_bytes: The raw byte content of the image.

    Returns:
        The byte content of the optimized image, or the original bytes if no optimization was needed.
    """
    # Check if image size exceeds the defined maximum.
    if len(image_bytes) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        logger.info(f"Image is larger than {MAX_IMAGE_SIZE_MB}MB, resizing...")
        img = Image.open(io.BytesIO(image_bytes))

        # Check if image dimensions exceed the maximum allowed.
        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            # `thumbnail` maintains aspect ratio while resizing to fit within the box.
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))

        # Re-compress the image to JPEG with a specific quality to reduce file size.
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        return buffer.getvalue()

    return image_bytes


def analyze_room_for_mess(image_base64: str) -> List[dict]:
    """
    Analyzes a base64-encoded image to identify mess using a configured AI service.

    This is the main entry point for the AI service. It orchestrates the entire
    process:
    1. Validates that an AI model is configured.
    2. Decodes and optimizes the input image to meet provider constraints.
    3. Sanitizes the user-defined prompt to prevent injection attacks.
    4. Selects the appropriate AI provider based on the model name.
    5. Calls the provider-specific analysis function.
    6. Returns the parsed list of tasks or raises an error.

    Args:
        image_base64: A string containing the base64-encoded image data.

    Returns:
        A list of dictionaries, where each dictionary represents a "mess"
        identified by the AI. Example: `[{"mess": "clothes on floor", "reason": "..."}]`

    Raises:
        ConfigError: If the AI model or a required API key is not configured.
        AIError: If the image is invalid, the AI call fails, or the response
                 cannot be parsed.
    """
    if not settings.ai_model:
        raise ConfigError("AI model not specified in configuration.")

    logger.info(f"Using AI model: {settings.ai_model}")

    # Step 1: Decode and optimize the image from base64.
    try:
        image_bytes = base64.b64decode(image_base64)
        optimized_image_bytes = _optimize_image(image_bytes)
        # Re-encode the (potentially smaller) image back to base64 for the API call.
        optimized_image_base64 = base64.b64encode(optimized_image_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to decode or optimize image: {e}", exc_info=True)
        raise AIError("Invalid image format or processing error.")

    # Step 2: Sanitize the prompt from settings.
    sanitized_prompt = _sanitize_prompt(settings.ai_prompt)

    # Step 3: Route to the correct AI provider based on the model name in settings.
    try:
        model_lower = settings.ai_model.lower()
        if "gemini" in model_lower or "google" in model_lower:
            # Ensure the required library is installed.
            if not genai:
                raise ConfigError("Google AI libraries not installed. Please run: pip install google-generativeai pillow")
            # Ensure the required API key is configured.
            if not settings.google_api_key:
                raise ConfigError("Google API key is not configured for Gemini model.")
            return _analyze_with_gemini(optimized_image_base64, sanitized_prompt)

        elif "gpt" in model_lower or "openai" in model_lower:
            # Ensure the required library is installed.
            if not openai:
                raise ConfigError("OpenAI library not installed. Please run: pip install openai")
            # Ensure the required API key is configured.
            if not settings.openai_api_key:
                raise ConfigError("OpenAI API key is not configured for GPT model.")
            return _analyze_with_openai(optimized_image_base64, sanitized_prompt)
        else:
            # If the model name doesn't match known providers, raise an error.
            raise AIError(f"Unsupported AI model: {settings.ai_model}")

    except Exception as e:
        # Catch-all for any other unexpected errors during the process.
        logger.error(f"Unexpected error during AI analysis: {e}", exc_info=True)
        raise AIError("An unexpected error occurred during analysis.") from e


def _analyze_with_gemini(image_base64: str, prompt: str) -> List[dict]:
    """
    Analyzes the image using the Google Gemini model.

    Handles the specific logic for authenticating with Google, preparing the
    request with the image and prompt, and interpreting the response.

    Args:
        image_base64: The base64-encoded image to analyze.
        prompt: The sanitized text prompt for the AI.

    Returns:
        A list of mess tasks parsed from the AI's response.

    Raises:
        AIError: If the API call to Gemini fails or returns an unexpected response.
    """
    global _gemini_configured
    if not genai:
        # This path should not be reachable due to checks in `analyze_room_for_mess`,
        # but it satisfies the type checker.
        raise ConfigError("Google AI libraries not installed. Please run: pip install google-generativeai pillow")

    try:
        # Configure the genai client with the API key, but only once per process.
        if not _gemini_configured and settings.google_api_key:
            genai.configure(api_key=settings.google_api_key.get_secret_value())
            _gemini_configured = True

        # The Gemini API requires the image as a PIL Image object, not base64.
        image_bytes = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(image_bytes))

        # Initialize the generative model and send the prompt and image.
        model = genai.GenerativeModel(settings.ai_model)
        response = model.generate_content([prompt, img])

        # Handle cases where the response was blocked for safety reasons.
        if not response.parts:
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                reason = f"Content blocked by Gemini. Reason: {response.prompt_feedback.block_reason}"
                logger.warning(reason)
                return [{"description": reason}]

            logger.warning("Gemini returned an empty but valid response.")
            return [{"description": "The AI returned an empty response, indicating no mess was found."}]

        # Extract text content from the response parts.
        text_content = "".join(
            part.text for part in response.parts if hasattr(part, "text")
        )
        if not text_content:
            raise AIError("Gemini returned a response with no text content.")

        logger.info(f"Raw Gemini response: {text_content}")
        return _parse_ai_response(text_content)

    except Exception as e:
        logger.error(f"Error with Gemini analysis: {e}", exc_info=True)
        raise AIError("Failed to analyze image with Gemini.") from e


def _analyze_with_openai(image_base64: str, prompt: str) -> List[dict]:
    """
    Analyzes the image using an OpenAI GPT model.

    Handles the specific logic for authenticating with OpenAI, constructing
    the chat completion request with the image and prompt, and interpreting
    the response.

    Args:
        image_base64: The base64-encoded image to analyze.
        prompt: The sanitized text prompt for the AI.

    Returns:
        A list of mess tasks parsed from the AI's response.

    Raises:
        ConfigError: If the OpenAI API key is missing.
        AIError: If the API call to OpenAI fails or returns an empty response.
    """
    if not openai:
        # This path should not be reachable due to checks in `analyze_room_for_mess`,
        # but it satisfies the type checker.
        raise ConfigError("OpenAI library not installed. Please run: pip install openai")

    try:
        if not settings.openai_api_key:
            raise ConfigError("OpenAI API key is not configured.")

        # Initialize the OpenAI client with the API key from settings.
        client = openai.OpenAI(api_key=settings.openai_api_key.get_secret_value())

        # Construct the payload for the chat completions API.
        response = client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        text_content = response.choices[0].message.content
        if not text_content:
            raise AIError("OpenAI returned an empty response.")

        logger.info(f"Raw OpenAI response: {text_content}")
        return _parse_ai_response(text_content)

    except Exception as e:
        logger.error(f"Error with OpenAI analysis: {e}", exc_info=True)
        raise AIError("Failed to analyze image with OpenAI.") from e


def _parse_ai_response(text_content: str) -> List[dict]:
    """
    Parses the AI's JSON response to extract a list of tasks.

    The AI is expected to return a JSON object with a "tasks" key. This function
    is designed to be resilient, handling common formatting issues like markdown
    code blocks and providing a fallback for older, simple list formats.

    Example expected JSON:
    `{"tasks": [{"mess": "clothes on floor", "reason": "Reduces cleanliness"}]}`

    Args:
        text_content: The raw text response from the AI model.

    Returns:
        A list of dictionaries representing the identified cleaning tasks.

    Raises:
        AIError: If the response cannot be parsed into the expected format.
    """
    logger.debug(f"Attempting to parse AI response: {text_content}")
    # Use regex to robustly extract JSON content from markdown code blocks (e.g., ```json ... ```).
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text_content)
    if match:
        text_content = match.group(1)

    try:
        data = json.loads(text_content.strip())

        # Primary case: A dictionary with a "tasks" key containing a list of objects.
        if isinstance(data, dict) and "tasks" in data:
            tasks = data["tasks"]
            if isinstance(tasks, list):
                # Validate that list items are dictionaries, as expected.
                if all(isinstance(item, dict) for item in tasks):
                    logger.info(f"Successfully parsed {len(tasks)} tasks.")
                    return tasks
                else:
                    # Handle cases where the AI returns a list of strings instead of objects.
                    logger.warning("Tasks in JSON are not formatted as objects. Attempting to convert.")
                    return [{"mess": str(item), "reason": "N/A"} for item in tasks]
            else:
                raise AIError("AI response's 'tasks' key is not a list.")

        # Fallback for older formats where the AI might just return a list directly.
        elif isinstance(data, list):
            logger.warning("AI returned a list instead of a dict. Converting to new format.")
            return [{"mess": str(item), "reason": "N/A"} for item in data]

        else:
            raise AIError("AI response is not a JSON object with a 'tasks' key.")

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON from AI response.", exc_info=True)
        # If JSON parsing fails, attempt a more lenient text-based parsing as a last resort.
        return _parse_text_response(text_content)
    except Exception as e:
        logger.error(f"Error parsing AI response: {e}", exc_info=True)
        raise AIError("Failed to parse the AI's response.")


def _parse_text_response(text: str) -> List[dict]:
    """
    Fallback parser for plain text responses when JSON parsing fails.

    This function attempts to extract meaningful tasks from a simple,
    line-delimited text response. It's a last resort to salvage a response
    that isn't in the expected JSON format.

    Args:
        text: The raw text response from the AI.

    Returns:
        A list of dictionaries, with each line converted into a task.
        Returns an empty list if no suitable lines are found to avoid errors.
    """
    logger.warning("Falling back to text-based parsing for AI response.")
    tasks = []
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        # Skip empty lines or lines that are likely part of JSON structure.
        if not line or line.startswith('#') or line.startswith('{') or line in ['```', '```json', 'tasks:']:
            continue

        # Clean up common list markers and punctuation from the line.
        line = line.lstrip('•-*[]"').rstrip('",').strip()

        # Add the line as a task if it seems substantial.
        if line and len(line) > 10:  # Basic filter for meaningful content.
            tasks.append({"mess": line, "reason": "Parsed from text"})

    if not tasks:
        logger.warning("Could not extract any tasks from text response.")
        # Return an empty list instead of raising an error to be more resilient.
        return []

    logger.info(f"Extracted {len(tasks)} tasks using fallback text parser.")
    # Limit to 10 tasks to avoid runaway responses.
    return tasks[:10]