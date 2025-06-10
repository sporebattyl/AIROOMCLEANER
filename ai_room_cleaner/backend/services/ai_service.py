import os
import io
import base64
import json
import logging
import google.generativeai as genai
from PIL import Image

def analyze_room_for_mess(image_base64):
    """
    Analyzes a base64-encoded image using Google Gemini and returns a list of cleaning tasks.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logging.error("Error: GOOGLE_API_KEY environment variable not set")
        return []

    try:
        genai.configure(api_key=api_key)

        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))

        model = genai.GenerativeModel('gemini-pro-vision')
        
        prompt = (
            "Identify and list any items that are out of place or contributing to messiness in the room. "
            "For each item, describe its location. Return the output as a JSON array of strings."
        )
        
        response = model.generate_content([prompt, image])
        
        # Extract JSON from the response text
        text_content = response.text
        if text_content.startswith("```json"):
            text_content = text_content.strip("```json\n").strip("```")
        
        messes = json.loads(text_content)
        return messes
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from Gemini response: {e}")
        logging.error(f"Received text for debugging: {text_content}")
        return []
    except Exception as e:
        logging.error(f"Error analyzing image with Gemini: {e}")
        return []