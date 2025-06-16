"""
Logging setup and middleware for the AI Room Cleaner application.
"""
import sys
import uuid

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


def setup_logging():
    """
    Set up structured logging for the application.
    """
    logger.remove()

    # Console logger
    logger.add(
        sys.stdout,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
        "{name}:{function}:{line} - {message}",
        colorize=True,
    )

    # File logger (JSON format)
    logger.add(
        "logs/app.log",
        level="DEBUG",
        format="{message}",
        serialize=True,
        rotation="100 MB",
        retention="30 days",
    )


class LoggingMiddleware(BaseHTTPMiddleware):  # pylint: disable=too-few-public-methods
    """
    Middleware that adds a unique request ID to each log entry.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        with logger.contextualize(request_id=request_id):
            response = await call_next(request)
        return response

logging_middleware = LoggingMiddleware  # pylint: disable=invalid-name
