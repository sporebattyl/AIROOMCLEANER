import json
import google.generativeai as genai
from app.config import Config

class AIService:
    """Service for interacting with AI models."""

    def __init__(self, config: Config):
        self.config = config
        if config.ai_provider == "Google Gemini":
            genai.configure(api_key=config.api_key)

    def analyze_image(self, image_data: bytes) -> dict:
        """Analyzes an image and returns a cleanliness score and a to-do list."""
        if self.config.ai_provider == "Google Gemini":
            return self._analyze_with_gemini(image_data)
        else:
            raise NotImplementedError(f"AI provider {self.config.ai_provider} is not supported.")

    def _analyze_with_gemini(self, image_data: bytes) -> dict:
        """Analyzes an image using the Google Gemini model."""
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        image_part = {"mime_type": "image/jpeg", "data": image_data}
        
        prompt = self.config.prompt or """
        Analyze the attached image of a room and provide a cleanliness score from 0 to 100, 
        where 100 is perfectly clean. Also, provide a to-do list of tasks to improve the score.
        Return the response as a JSON object with the keys "cleanliness_score" and "todo_list".
        The todo_list should be an array of strings.
        """

        response = model.generate_content([prompt, image_part])
        
        try:
            # The response text should be a JSON string, possibly with markdown backticks
            clean_response = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(clean_response)
            # Basic validation
            if "cleanliness_score" in data and "todo_list" in data:
                return data
            else:
                raise ValueError("Invalid JSON structure from AI")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing AI response: {e}")
            return {"cleanliness_score": 0, "todo_list": []}
