import asyncio
from typing import List, Dict, Any

class AppState:
    """A thread-safe class to manage application state."""
    def __init__(self):
        self._latest_tasks: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def get_tasks(self) -> List[Dict[str, Any]]:
        """Get the current list of cleaning tasks."""
        async with self._lock:
            return self._latest_tasks

    async def set_tasks(self, tasks: List[Dict[str, Any]]):
        """Set the list of cleaning tasks."""
        async with self._lock:
            self._latest_tasks = tasks

# Singleton instance to be used across the application
app_state = AppState()