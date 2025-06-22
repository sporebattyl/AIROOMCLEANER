import sys
from loguru import logger
from .config import settings

def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL.upper(),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
    return logger

log = setup_logging()
