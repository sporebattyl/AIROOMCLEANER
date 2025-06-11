from typing import List, Optional

class AppState:
    """A thread-safe class to manage application state."""
    def __init__(self):
        self._latest_tasks: List[str] = []

    def get_tasks(self) -> List[str]:
        """Get the current list of cleaning tasks."""
        return self._latest_tasks

    def set_tasks(self, tasks: List[str]):
        """Set the list of cleaning tasks."""
        self._latest_tasks = tasks

# Singleton instance to be used across the application
app_state = AppState()