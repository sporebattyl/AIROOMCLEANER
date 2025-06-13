import asyncio
from typing import List, Dict, Any

from backend.services.ai_service import AIService


class State:
    """A class to manage shared application resources."""

    def __init__(self, ai_service: AIService):
        """
        Initializes the State with all necessary services.
        Args:
            ai_service: An instance of the AIService.
        """
        self.ai_service = ai_service