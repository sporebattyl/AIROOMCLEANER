"""
This module provides a service for managing the analysis history.
"""
from typing import List, Dict, Any
from loguru import logger

class HistoryService:
    """
    Manages the storage and retrieval of analysis history in-memory.
    
    In a production environment, this would be replaced with a persistent
    database connection (e.g., PostgreSQL, MongoDB).
    """
    def __init__(self):
        self._history: List[Dict[str, Any]] = []
        logger.info("HistoryService initialized with in-memory storage.")

    async def add_to_history(self, analysis_result: Dict[str, Any]):
        """Adds a new analysis result to the history."""
        self._history.append(analysis_result)
        logger.info(f"Added item to history. History now contains {len(self._history)} items.")

    async def get_history(self) -> List[Dict[str, Any]]:
        """Returns the entire analysis history."""
        logger.info(f"Retrieving {len(self._history)} items from history.")
        return self._history

    async def clear_history(self):
        """Clears the entire analysis history."""
        count = len(self._history)
        self._history.clear()
        logger.info(f"History cleared. Removed {count} items.")
