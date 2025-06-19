from abc import ABC, abstractmethod
from typing import Dict, Any
from core.config import Settings, AIProvider as AIProviderEnum
import openai

class AIProvider(ABC):
    """
    Abstract base class for AI providers.
    """

    @abstractmethod
    async def analyze_image(self, image_base64: str, model: str) -> Dict[str, Any]:
        """
        Analyzes an image to determine room cleanliness.
        """
        pass

class OpenAIProvider(AIProvider):
    """
    AI provider for OpenAI models.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        openai.api_key = self.settings.current_api_key.get_secret_value()

    async def analyze_image(self, image_base64: str, model: str) -> Dict[str, Any]:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What’s in this image?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        import json
        content = response.choices[0].message.content
        if content:
            return json.loads(content)
        return {"cleanliness_score": 0, "todo_list": []}

def get_ai_provider(settings: Settings) -> AIProvider:
    """
    Returns an AI provider based on the settings.
    """
    if settings.AI_PROVIDER == AIProviderEnum.OPENAI:
        return OpenAIProvider(settings)
    else:
        raise ValueError(f"Invalid AI provider: {settings.AI_PROVIDER}")
