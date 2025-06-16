"""Custom middleware for the AI Room Cleaner backend."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


def request_size_limit_middleware(app: ASGIApp, max_size: int):
    """
    Factory function to create a middleware that limits the size of incoming request bodies.
    """

    async def middleware(scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http" and scope["method"] == "POST":
            request = Request(scope, receive)
            content_length = request.headers.get("content-length")

            if content_length is None:
                response = JSONResponse(
                    {"detail": "Content-Length header required."}, status_code=411
                )
                await response(scope, receive, send)
                return

            if int(content_length) > max_size:
                response = JSONResponse(
                    {"detail": "Payload too large."}, status_code=413
                )
                await response(scope, receive, send)
                return

        await app(scope, receive, send)

    return middleware
