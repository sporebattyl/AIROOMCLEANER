import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import AIProviderError, ConfigError
from app.core.logging import InterceptHandler, logger
from app.core.middleware import RateLimitingMiddleware
from app.services.ai_service import AIService
from app.services.ha_service import HomeAssistantService

# Configure logging
logging.getLogger().handlers = [InterceptHandler()]
logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
logger.configure(handlers=[{"sink": "logs/app.log", "level": settings.LOG_LEVEL, "rotation": "10 MB"}])

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    """
    logger.info("Starting AI Room Cleaner...")
    
    # Initialize services
    app.state.ha_service = HomeAssistantService()
    app.state.ai_service = AIService(settings)
    
    yield
    
    logger.info("Shutting down AI Room Cleaner...")

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title="AI Room Cleaner",
        description="A Home Assistant addon that uses AI to analyze room cleanliness.",
        version="1.0.2",
        lifespan=lifespan,
    )

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # app.add_middleware(
    #     RateLimitingMiddleware,
    #     limit=settings.RATE_LIMIT_PER_MINUTE,
    #     block_duration=settings.RATE_LIMIT_BLOCK_DURATION_MINUTES,
    # )

    # Add exception handlers
    @app.exception_handler(AIProviderError)
    async def ai_provider_error_handler(request: Request, exc: AIProviderError):
        return JSONResponse(
            status_code=503,
            content={"error": "AI_SERVICE_ERROR", "message": exc.detail},
        )

    @app.exception_handler(ConfigError)
    async def config_error_handler(request: Request, exc: ConfigError):
        return JSONResponse(
            status_code=500,
            content={"error": "CONFIGURATION_ERROR", "message": exc.detail},
        )

    return app

app = create_app()