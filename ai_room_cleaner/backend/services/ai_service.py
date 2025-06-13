import base64
import io
import json
import logging
import re
from typing import List
import bleach
from PIL import Image

# Optional dependency imports
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

MAX_IMAGE_SIZE_MB = 1
MAX_IMAGE_DIMENSION = 2048

_gemini_configured = False

def _sanitize_prompt(prompt: str) -> str:
    """Sanitizes the AI prompt to remove potentially harmful content."""
    return bleach.clean(prompt, tags=[], attributes={}, strip=True)

def _optimize_image(image_bytes: bytes) -> bytes:
    """
    Resizes an image if it's too large, either by file size or dimensions.
    """
    if len(image_bytes) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        logger.info(f"Image is larger than {MAX_IMAGE_SIZE_MB}MB, resizing...")
        img = Image.open(io.BytesIO(image_bytes))
        
        # Resize based on a max dimension to avoid overly large images
        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))
        
        # Re-compress to reduce size
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        return buffer.getvalue()
        
    return image_bytes

def analyze_room_for_mess(image_base64: str) -> List[dict]:
    """
    Analyzes a base64-encoded image using the configured AI service.
    Raises:
        ConfigError: If the AI model or API key is not configured.
        AIError: If the analysis fails for any reason.
    """
    if not settings.ai_model:
        raise ConfigError("AI model not specified in configuration.")

    logger.info(f"Using AI model: {settings.ai_model}")
    
    # Decode and optimize the image
    try:
        image_bytes = base64.b64decode(image_base64)
        optimized_image_bytes = _optimize_image(image_bytes)
        optimized_image_base64 = base64.b64encode(optimized_image_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to decode or optimize image: {e}", exc_info=True)
        raise AIError("Invalid image format or processing error.")

    # Sanitize the prompt
    sanitized_prompt = _sanitize_prompt(settings.ai_prompt)

    try:
        model_lower = settings.ai_model.lower()
        if "gemini" in model_lower or "google" in model_lower:
            if not genai:
                raise ConfigError("Google AI libraries not installed. Please run: pip install google-generativeai pillow")
            if not settings.google_api_key:
                raise ConfigError("Google API key is not configured for Gemini model.")
            return _analyze_with_gemini(optimized_image_base64, sanitized_prompt)

        elif "gpt" in model_lower or "openai" in model_lower:
            if not openai:
                raise ConfigError("OpenAI library not installed. Please run: pip install openai")
            if not settings.openai_api_key:
                raise ConfigError("OpenAI API key is not configured for GPT model.")
            return _analyze_with_openai(optimized_image_base64, sanitized_prompt)
        else:
            raise AIError(f"Unsupported AI model: {settings.ai_model}")

    except Exception as e:
        logger.error(f"Unexpected error during AI analysis: {e}", exc_info=True)
        raise AIError("An unexpected error occurred during analysis.") from e

def _analyze_with_gemini(image_base64: str, prompt: str) -> List[dict]:
    """Analyze image using Google Gemini."""
    global _gemini_configured
    try:
        if not _gemini_configured and settings.google_api_key:
            genai.configure(api_key=settings.google_api_key.get_secret_value())
            _gemini_configured = True

        image_bytes = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(image_bytes))

        model = genai.GenerativeModel(settings.ai_model)
        response = model.generate_content([prompt, img])

        if not response.parts:
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                reason = f"Content blocked by Gemini. Reason: {response.prompt_feedback.block_reason}"
                logger.warning(reason)
                return [{"description": reason}]
            
            logger.warning("Gemini returned an empty but valid response.")
            return [{"description": "The AI returned an empty response, indicating no mess was found."}]

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
    """Analyze image using OpenAI GPT."""
    try:
        if not settings.openai_api_key:
            raise ConfigError("OpenAI API key is not configured.")
        
        client = openai.OpenAI(api_key=settings.openai_api_key.get_secret_value())

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
    Parse the AI's JSON response to extract a list of tasks.
    The AI is expected to return a JSON object with a "tasks" key,
    which contains a list of objects, where each object has a "mess" and "reason" key.
    Example: {"tasks": [{"mess": "clothes on floor", "reason": "Reduces cleanliness"}]}
    """
    logger.debug(f"Attempting to parse AI response: {text_content}")
    # Use regex to robustly extract content from markdown code blocks
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text_content)
    if match:
        text_content = match.group(1)

    try:
        data = json.loads(text_content.strip())
        
        if isinstance(data, dict) and "tasks" in data:
            tasks = data["tasks"]
            if isinstance(tasks, list):
                # Validate that tasks are dicts, not strings
                if all(isinstance(item, dict) for item in tasks):
                    logger.info(f"Successfully parsed {len(tasks)} tasks.")
                    return tasks
                else:
                    logger.warning("Tasks in JSON are not formatted as objects. Attempting to convert.")
                    return [{"mess": str(item), "reason": "N/A"} for item in tasks]
            else:
                raise AIError("AI response's 'tasks' key is not a list.")
        
        # Fallback for older list-based format
        elif isinstance(data, list):
            logger.warning("AI returned a list instead of a dict. Converting to new format.")
            return [{"mess": str(item), "reason": "N/A"} for item in data]
            
        else:
            raise AIError("AI response is not a JSON object with a 'tasks' key.")

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON from AI response.", exc_info=True)
        # Try a more lenient text-based parsing as a last resort
        return _parse_text_response(text_content)
    except Exception as e:
        logger.error(f"Error parsing AI response: {e}", exc_info=True)
        raise AIError("Failed to parse the AI's response.")

def _parse_text_response(text: str) -> List[dict]:
    """Fallback parser for plain text responses."""
    logger.warning("Falling back to text-based parsing for AI response.")
    tasks = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('{') or line in ['```', '```json', 'tasks:']:
            continue
        
        # Remove list markers
        line = line.lstrip('•-*[]"').rstrip('",').strip()
        
        if line and len(line) > 10:  # Basic filter
            tasks.append({"mess": line, "reason": "Parsed from text"})
    
    if not tasks:
        logger.warning("Could not extract any tasks from text response.")
        # Return an empty list instead of raising an error, to be more resilient
        return []
    
    logger.info(f"Extracted {len(tasks)} tasks using fallback text parser.")
    return tasks[:10]