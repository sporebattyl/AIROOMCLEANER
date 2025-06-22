import json
import aiofiles
from app.core.logging import log

HISTORY_FILE = "/data/history.json"

class HistoryService:
    async def get_history(self) -> list:
        try:
            async with aiofiles.open(HISTORY_FILE, mode="r") as f:
                contents = await f.read()
                return json.loads(contents)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    async def add_record(self, record: dict):
        history = await self.get_history()
        history.append(record)
        try:
            async with aiofiles.open(HISTORY_FILE, mode="w") as f:
                await f.write(json.dumps(history, indent=2))
            log.info("Successfully wrote analysis record to history.")
        except Exception as e:
            log.error(f"Failed to write to history file: {e}")
