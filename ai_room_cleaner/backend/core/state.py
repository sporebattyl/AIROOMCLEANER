import asyncio
import json
import os
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from loguru import logger

from backend.services.history_service import HistoryService
from backend.core.config import AppSettings

if TYPE_CHECKING:
    from backend.services.ai_service import AIService


_state: Optional["State"] = None


class State:
    """A class to manage shared application resources."""

    def __init__(self, ai_service: "AIService", history_service: HistoryService, settings: AppSettings):
        """
        Initializes the State with services.
        Args:
            ai_service: An instance of the AIService.
            history_service: An instance of the HistoryService.
            settings: The application settings object.
        """
        self.ai_service = ai_service
        self.history_service = history_service
        self.settings = settings


def get_state() -> "State":
    """
    Returns the singleton instance of the State.
    This function is the single point of access for the application state.
    """
    global _state
    if _state is None:
        raise RuntimeError("State has not been initialized. Call initialize_state first.")
    return _state


async def initialize_state(ai_service: "AIService", history_service: HistoryService, settings: AppSettings) -> "State":
    """
    Initializes the application state. This should be called once at startup.
    """
    global _state
    if _state is not None:
        logger.warning("State is already initialized. Ignoring subsequent call.")
        return _state

    logger.info("Initializing application state.")
    _state = State(ai_service, history_service, settings)
    return _state