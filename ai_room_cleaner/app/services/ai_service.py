import base64
import httpx
from app.core.config import settings
from app.core.exceptions import AIProviderError
from app.core.logging import log

class AIService:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.model = settings.AI_MODEL
        self.prompt = settings.PROMPT
        self.api_key = self._get_api_key()

    def _get_api_key(self) -> str:
        if self.provider == "openai":
            key = settings.OPENAI_API_KEY
        elif self.provider == "google":
            key = settings.GOOGLE_API_KEY
        else:
            raise AIProviderError(f"Unsupported AI provider: {self.provider}")
        if not key:
            raise AIProviderError(f"API key for {self.provider} is not configured.")
        return key

    async def analyze_image(self, image_bytes: bytes) -> dict:
        log.info(f"Analyzing image using {self.provider} with model {self.model}")
        if self.provider == "openai":
            return await self._analyze_with_openai(image_bytes)
        elif self.provider == "google":
            return await self._analyze_with_google(image_bytes)
        else:
            raise AIProviderError(f"Unsupported AI provider: {self.provider}")

    async def _analyze_with_openai(self, image_bytes: bytes) -> dict:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            "max_tokens": 300,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if response.status_code != 200:
                raise AIProviderError(f"OpenAI API error: {response.status_code} - {response.text}")
            return response.json()

    async def _analyze_with_google(self, image_bytes: bytes) -> dict:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": self.prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}},
                    ]
                }
            ]
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=30)
            if response.status_code != 200:
                raise AIProviderError(f"Google API error: {response.status_code} - {response.text}")
            return response.json()
