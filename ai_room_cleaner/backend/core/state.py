import asyncio
import json
import os
from typing import List, Dict, Any
from loguru import logger

from backend.services.ai_service import AIService
from backend.core.config import Settings


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

    def add_analysis_to_history(self, analysis: Dict[str, Any]):
        """Adds a new analysis result to the history and saves it."""
        self.history.insert(0, analysis)
        # Keep history to a reasonable size
        if len(self.history) > 50:
            self.history = self.history[:50]
        self.save_history()

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns the current analysis history."""
        return self.history

    def save_history(self):
        """Saves the current analysis history to a JSON file."""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "w") as f:
                json.dump(self.history, f, indent=2)
            logger.info(f"Saved {len(self.history)} history items to {self.history_file}")
        except Exception as e:
            logger.error(f"Failed to save history to {self.history_file}: {e}", exc_info=True)

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