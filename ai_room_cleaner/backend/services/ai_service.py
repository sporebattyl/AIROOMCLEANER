import os
import io
import base64
import json
import logging
from typing import List

logger = logging.getLogger(__name__)

def analyze_room_for_mess(image_base64: str) -> List[str]:
    """
    Analyzes a base64-encoded image using Google Gemini and returns a list of cleaning tasks.
    """
    # Check for API key - could be GOOGLE_API_KEY or OPENAI_API_KEY
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
    ai_model = os.getenv("AI_MODEL", "gemini-2.5-pro")
    
    if not api_key:
        logger.error("Error: Neither GOOGLE_API_KEY nor OPENAI_API_KEY environment variable is set")
        return ["Configuration Error: API key not provided"]

    logger.info(f"Using AI model: {ai_model}")

    try:
        # Import here to avoid import errors if packages aren't available
        if "gemini" in ai_model.lower() or "google" in ai_model.lower():
            return _analyze_with_gemini(image_base64, api_key, ai_model)
        elif "gpt" in ai_model.lower() or "openai" in ai_model.lower():
            return _analyze_with_openai(image_base64, api_key, ai_model)
        else:
            logger.error(f"Unsupported AI model: {ai_model}")
            return [f"Error: Unsupported AI model '{ai_model}'"]
            
    except ImportError as e:
        logger.error(f"Required AI library not available: {e}")
        return [f"Configuration Error: Required AI library not installed"]
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return [f"Analysis Error: {str(e)}"]

def _analyze_with_gemini(image_base64: str, api_key: str, model_name: str) -> List[str]:
    """Analyze image using Google Gemini"""
    try:
        import google.generativeai as genai
        from PIL import Image
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Decode image
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Use the correct model name
        model_name = model_name if "vision" in model_name else "gemini-1.5-pro"
        model = genai.GenerativeModel(model_name)
        
        prompt = os.getenv("PROMPT", 
            "Analyze this room image and identify any items that are out of place or contributing to messiness. "
            "For each item, describe what needs to be cleaned or organized. "
            "Return the output as a JSON array of strings, with each string being a specific cleaning task."
        )
        
        response = model.generate_content([prompt, image])
        
        # Extract JSON from the response text
        text_content = response.text
        logger.info(f"Raw AI response: {text_content}")
        
        # Handle markdown code blocks
        if "```json" in text_content:
            start_index = text_content.find("```json") + len("```json")
            end_index = text_content.rfind("```")
            if end_index > start_index:
                text_content = text_content[start_index:end_index]
        elif "```" in text_content:
            # Handle generic code blocks
            start_index = text_content.find("```") + 3
            end_index = text_content.rfind("```")
            if end_index > start_index:
                text_content = text_content[start_index:end_index]
        
        # Try to parse as JSON
        try:
            messes = json.loads(text_content.strip())
            if isinstance(messes, list):
                return messes
            else:
                logger.warning("AI response was not a list, converting...")
                return [str(messes)]
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract meaningful tasks from text
            logger.warning("Failed to parse JSON, extracting tasks from text...")
            return _parse_text_response(text_content)
            
    except Exception as e:
        logger.error(f"Error with Gemini analysis: {e}")
        return [f"Gemini Analysis Error: {str(e)}"]

def _analyze_with_openai(image_base64: str, api_key: str, model_name: str) -> List[str]:
    """Analyze image using OpenAI GPT"""
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key)
        
        prompt = os.getenv("PROMPT",
            "Analyze this room image and identify any items that are out of place or contributing to messiness. "
            "For each item, describe what needs to be cleaned or organized. "
            "Return the output as a JSON array of strings, with each string being a specific cleaning task."
        )
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        text_content = response.choices[0].message.content
        logger.info(f"Raw AI response: {text_content}")
        
        # Try to parse as JSON
        try:
            messes = json.loads(text_content.strip())
            if isinstance(messes, list):
                return messes
            else:
                return [str(messes)]
        except json.JSONDecodeError:
            # If JSON parsing fails, extract tasks from text
            return _parse_text_response(text_content)
            
    except Exception as e:
        logger.error(f"Error with OpenAI analysis: {e}")
        return [f"OpenAI Analysis Error: {str(e)}"]

def _parse_text_response(text: str) -> List[str]:
    """Parse text response to extract cleaning tasks"""
    tasks = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        # Skip empty lines and common markdown elements
        if not line or line.startswith('#') or line in ['```', '```json']:
            continue
        
        # Remove bullet points and numbering
        line = line.lstrip('•-*').strip()
        if line.startswith(tuple('0123456789')):
            # Remove numbering like "1. ", "2. ", etc.
            line = line.split('.', 1)[-1].strip()
        
        if len(line) > 10:  # Only add substantial tasks
            tasks.append(line)
    
    if not tasks:
        # If no tasks found, return a default message
        return ["No specific cleaning tasks identified, but consider general tidying"]
    
    return tasks[:10]  # Limit to 10 tasks max