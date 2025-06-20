import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int, block_duration: int):
        super().__init__(app)
        self.limit = limit
        self.block_duration = block_duration
        self.requests = {}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        if client_ip in self.requests:
            if current_time - self.requests[client_ip]["timestamp"] < self.block_duration:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "TOO_MANY_REQUESTS",
                        "message": "Too many requests. Please try again later.",
                    },
                )
            else:
                self.requests[client_ip] = {"count": 1, "timestamp": current_time}
        else:
            self.requests[client_ip] = {"count": 1, "timestamp": current_time}

        if self.requests[client_ip]["count"] > self.limit:
            self.requests[client_ip]["timestamp"] = current_time
            return JSONResponse(
                status_code=429,
                content={
                    "error": "TOO_MANY_REQUESTS",
                    "message": "Too many requests. Please try again later.",
                },
            )

        self.requests[client_ip]["count"] += 1
        return await call_next(request)
