import logging
import sys
from loguru import logger as loguru_logger

class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages and redirect them to Loguru.
    """
    def emit(self, record):
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

logger = loguru_logger
logger.remove()
logger.add(sys.stderr, level="INFO")