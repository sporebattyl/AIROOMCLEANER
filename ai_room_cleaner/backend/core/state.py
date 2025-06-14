import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from loguru import logger

from backend.services.ai_service import AIService
from backend.core.config import Settings


_state: Optional["State"] = None


class State:
    """A class to manage shared application resources and history."""

    def __init__(self, ai_service: AIService, settings: Settings):
        """
        Initializes the State with services and loads history from disk.
        Args:
            ai_service: An instance of the AIService.
            settings: The application settings object.
        """
        self.ai_service = ai_service
        self.history_file = settings.history_file_path
        self.history: List[Dict[str, Any]] = []
        self.load_history()

    async def add_analysis_to_history(self, analysis: Dict[str, Any]):
        """Adds a new analysis result to the history and saves it."""
        self.history.insert(0, analysis)
        # Keep history to a reasonable size
        if len(self.history) > 50:
            self.history = self.history[:50]
        await self.save_history()

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns the current analysis history."""
        return self.history

    async def save_history(self):
        """Saves the analysis history to a file asynchronously."""
        try:
            import aiofiles
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            async with aiofiles.open(self.history_file, "w") as f:
                await f.write(json.dumps(self.history, indent=2))
        except Exception as e:
            logger.error(f"Failed to save history: {e}", exc_info=True)

    def load_history(self):
        """Loads analysis history from a JSON file."""
        if not os.path.exists(self.history_file):
            logger.info(f"History file not found at {self.history_file}. Starting with an empty history.")
            return
        try:
            with open(self.history_file, "r") as f:
                self.history = json.load(f)
            logger.info(f"Loaded {len(self.history)} history items from {self.history_file}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to load or parse history from {self.history_file}: {e}", exc_info=True)
            self.history = []


def get_state() -> "State":
    """
    Returns the singleton instance of the State.
    This function is the single point of access for the application state.
    """
    global _state
    if _state is None:
        raise RuntimeError("State has not been initialized. Call initialize_state first.")
    return _state


def initialize_state(ai_service: AIService, settings: Settings) -> "State":
    """
    Initializes the application state. This should be called once at startup.
    """
    global _state
    if _state is not None:
        logger.warning("State is already initialized. Ignoring subsequent call.")
        return _state

    logger.info("Initializing application state.")
    _state = State(ai_service, settings)
    return _state