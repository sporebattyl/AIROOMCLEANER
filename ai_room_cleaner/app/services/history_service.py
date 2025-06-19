import json
from typing import List, Dict, Any
from core.config import settings

class HistoryService:
    """
    Service for managing the analysis history.
    """

    def __init__(self):
        self.history_file = settings.HISTORY_FILE_PATH

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Gets the analysis history.
        """
        import os
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def add_to_history(self, item: Dict[str, Any]):
        """
        Adds an item to the analysis history.
        """
        import os
        if not os.path.exists(os.path.dirname(self.history_file)):
            os.makedirs(os.path.dirname(self.history_file))
        history = self.get_history()
        history.insert(0, item)
        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=4)
