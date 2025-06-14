import asyncio
import json
import os
from typing import List, Dict, Any
from loguru import logger

from backend.services.ai_service import AIService

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "analysis_history.json")

class State:
    """A class to manage shared application resources and history."""

    def __init__(self, ai_service: AIService):
        """
        Initializes the State with services and loads history from disk.
        Args:
            ai_service: An instance of the AIService.
        """
        self.ai_service = ai_service
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
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            with open(HISTORY_FILE, "w") as f:
                json.dump(self.history, f, indent=2)
            logger.info(f"Saved {len(self.history)} history items to {HISTORY_FILE}")
        except Exception as e:
            logger.error(f"Failed to save history to {HISTORY_FILE}: {e}", exc_info=True)

    def load_history(self):
        """Loads analysis history from a JSON file."""
        if not os.path.exists(HISTORY_FILE):
            logger.info("History file not found. Starting with an empty history.")
            return
        try:
            with open(HISTORY_FILE, "r") as f:
                self.history = json.load(f)
            logger.info(f"Loaded {len(self.history)} history items from {HISTORY_FILE}")
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to load or parse history from {HISTORY_FILE}: {e}", exc_info=True)
            self.history = []