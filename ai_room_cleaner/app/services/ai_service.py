import base64
from typing import Dict, Any, List
from app.core.config import Settings
from app.core.exceptions import AIError
from app.services.ai_providers import AIProvider, get_ai_provider

class AIService:
    """
    Service for interacting with AI models.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.ai_provider: AIProvider = get_ai_provider(settings)

    async def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyzes an image to determine room cleanliness.
        """
        try:
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            model = self.settings.OPENAI_MODEL if self.settings.AI_PROVIDER == "openai" else self.settings.GOOGLE_MODEL
            response = await self.ai_provider.analyze_image(image_base64, model)
            return self._parse_ai_response(response)
        except Exception as e:
            raise AIError(f"Failed to analyze image: {e}") from e

    def _parse_ai_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses the AI response to extract the cleanliness score and to-do list.
        """
        # This is a placeholder implementation.
        # The actual implementation will depend on the AI provider's response format.
        cleanliness_score = response.get("cleanliness_score", 0)
        todo_list = response.get("todo_list", [])
        return {"cleanliness_score": cleanliness_score, "todo_list": todo_list}
