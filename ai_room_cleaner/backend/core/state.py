"""
Manages the shared application state for the AI Room Cleaner.
"""
from typing import Optional, TYPE_CHECKING
from contextlib import asynccontextmanager

from loguru import logger

from .config import AppSettings
from ..services.history_service import HistoryService

if TYPE_CHECKING:
    from ai_room_cleaner.backend.services.ai_service import AIService


class _AppState:  # pylint: disable=too-few-public-methods
    """A class to manage shared application resources."""

    def __init__(self):
        self.ai_service: Optional["AIService"] = None
        self.history_service: Optional[HistoryService] = None
        self.settings: Optional[AppSettings] = None

    def initialize(
        self,
        ai_service: "AIService",
        history_service: HistoryService,
        settings: AppSettings,
    ):
        """Initializes the application state."""
        if self.settings is not None:
            logger.warning("State is already initialized. Ignoring subsequent call.")
            return
        self.ai_service = ai_service
        self.history_service = history_service
        self.settings = settings
        logger.info("Application state initialized.")


APP_STATE = _AppState()


def get_state() -> _AppState:
    """Returns the application state instance."""
    return APP_STATE


@asynccontextmanager
async def initialize_state(
    ai_service: "AIService", history_service: HistoryService, settings: AppSettings
):
    """Initializes and tears down the application state."""
    APP_STATE.initialize(ai_service, history_service, settings)
    yield
    logger.info("Application state torn down.")
