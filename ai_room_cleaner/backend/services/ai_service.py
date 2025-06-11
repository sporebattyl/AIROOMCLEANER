import io
import base64
import json
import logging
from typing import List
from backend.core.config import settings
from backend.core.exceptions import AIError, ConfigError

logger = logging.getLogger(__name__)

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

    try:
        model_lower = settings.ai_model.lower()
        if "gemini" in model_lower or "google" in model_lower:
            if not settings.google_api_key:
                raise ConfigError("Google API key is not configured for Gemini model.")
            return _analyze_with_gemini(image_base64)
        elif "gpt" in model_lower or "openai" in model_lower:
            if not settings.openai_api_key:
                raise ConfigError("OpenAI API key is not configured for GPT model.")
            return _analyze_with_openai(image_base64)
        else:
            raise AIError(f"Unsupported AI model: {settings.ai_model}")
            
    except ImportError as e:
        logger.error(f"Required AI library not available: {e}")
        raise ConfigError(f"Required AI library not installed for {settings.ai_model}") from e
    except Exception as e:
        logger.error(f"Unexpected error during AI analysis: {e}", exc_info=True)
        raise AIError("An unexpected error occurred during analysis.") from e

def _analyze_with_gemini(image_base64: str) -> List[dict]:
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

def _analyze_with_openai(image_base64: str) -> List[dict]:
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

def _parse_ai_response(text_content: str) -> List[dict]:
    """
    Parse the AI's JSON response to extract a list of tasks.
    The AI is expected to return a JSON object with a "tasks" key,
    which contains a list of objects, where each object has a "mess" and "reason" key.
    Example: {"tasks": [{"mess": "clothes on floor", "reason": "Reduces cleanliness"}]}
    """
    logger.debug(f"Attempting to parse AI response: {text_content}")
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