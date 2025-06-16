"""Custom middleware for the AI Room Cleaner backend."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

# pylint: disable=too-few-public-methods
class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log incoming requests and outgoing responses."""
    async def dispatch(self, request: Request, call_next):
        """Log request and response."""
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response

# pylint: disable=too-few-public-methods
class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit the size of incoming request payloads."""
    def __init__(self, app: ASGIApp, max_size: int):
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            content_length = request.headers.get("content-length")

            if content_length is None:
                return JSONResponse(
                    {"detail": "Content-Length header required."}, status_code=411
                )

            if int(content_length) > self.max_size:
                return JSONResponse(
                    {"detail": "Payload too large."}, status_code=413
                )

        return await call_next(request)
