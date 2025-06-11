import io
import base64
import json
import logging
from typing import List
from backend.core.config import settings
from backend.core.exceptions import AIError, ConfigError

logger = logging.getLogger(__name__)

def analyze_room_for_mess(image_base64: str) -> List[str]:
    """
    Analyzes a base64-encoded image using the configured AI service.
    Raises:
        ConfigError: If the AI model or API key is not configured.
        AIError: If the analysis fails for any reason.
    """
    if not settings.api_key:
        raise ConfigError("API key not configured for AI service.")
    if not settings.ai_model:
        raise ConfigError("AI model not specified in configuration.")

    logger.info(f"Using AI model: {settings.ai_model}")

    try:
        if "gemini" in settings.ai_model.lower() or "google" in settings.ai_model.lower():
            return _analyze_with_gemini(image_base64)
        elif "gpt" in settings.ai_model.lower() or "openai" in settings.ai_model.lower():
            return _analyze_with_openai(image_base64)
        else:
            raise AIError(f"Unsupported AI model: {settings.ai_model}")
            
    except ImportError as e:
        logger.error(f"Required AI library not available: {e}")
        raise ConfigError(f"Required AI library not installed for {settings.ai_model}") from e
    except Exception as e:
        logger.error(f"Unexpected error during AI analysis: {e}", exc_info=True)
        raise AIError("An unexpected error occurred during analysis.") from e

def _analyze_with_gemini(image_base64: str) -> List[str]:
    """Analyze image using Google Gemini."""
    try:
        import google.generativeai as genai
        from PIL import Image
        
        genai.configure(api_key=settings.google_api_key)
        
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        
        model = genai.GenerativeModel(settings.ai_model)
        
        response = model.generate_content([settings.ai_prompt, image])
        
        # The .text property can raise a ValueError if no text is found.
        # It's better to access parts and handle it gracefully.
        if not response.parts:
            raise AIError("Gemini returned an empty response.")
        
        text_content = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
        if not text_content:
            raise AIError("Gemini returned a response with no text content.")

        logger.info(f"Raw Gemini response: {text_content}")
        
        return _parse_ai_response(text_content)
            
    except Exception as e:
        logger.error(f"Error with Gemini analysis: {e}", exc_info=True)
        raise AIError("Failed to analyze image with Gemini.") from e

def _analyze_with_openai(image_base64: str) -> List[str]:
    """Analyze image using OpenAI GPT."""
    try:
        import openai
        
        client = openai.OpenAI(api_key=settings.openai_api_key)
        
        response = client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": settings.ai_prompt},
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

def _parse_ai_response(text_content: str) -> List[str]:
    """Parse the AI's response to extract a list of tasks."""
    # Handle markdown code blocks
    if "```json" in text_content:
        start_index = text_content.find("```json") + len("```json")
        end_index = text_content.rfind("```")
        if end_index > start_index:
            text_content = text_content[start_index:end_index]
    elif "```" in text_content:
        start_index = text_content.find("```") + 3
        end_index = text_content.rfind("```")
        if end_index > start_index:
            text_content = text_content[start_index:end_index]

    try:
        messes = json.loads(text_content.strip())
        if isinstance(messes, list):
            return [str(item) for item in messes]
        else:
            logger.warning("AI response was not a list, wrapping in a list.")
            return [str(messes)]
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON, attempting to extract tasks from text.")
        return _parse_text_response(text_content)

def _parse_text_response(text: str) -> List[str]:
    """Fallback parser for plain text responses."""
    tasks = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line in ['```', '```json']:
            continue
        
        line = line.lstrip('•-*').strip()
        if line and len(line) > 10:  # Basic filter for meaningful tasks
            tasks.append(line)
    
    if not tasks:
        raise AIError("AI returned an empty or unparseable response.")
    
    return tasks[:10]  # Limit to 10 tasks max