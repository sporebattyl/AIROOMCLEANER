from fastapi import HTTPException

class AppException(HTTPException):
    """Base class for application-specific exceptions."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class ImageProcessingError(AppException):
    """Exception raised for errors in the image processing."""
    def __init__(self, detail: str = "Error processing image."):
        super().__init__(status_code=500, detail=detail)

class AIProviderError(AppException):
    """Exception raised for errors related to the AI provider."""
    def __init__(self, detail: str = "Error from AI provider."):
        super().__init__(status_code=502, detail=detail)

class ConfigError(AppException):
    """Exception raised for configuration errors."""
    def __init__(self, detail: str = "Configuration error."):
        super().__init__(status_code=500, detail=detail)

class CameraError(AppException):
    """Exception raised for camera-related errors."""
    def __init__(self, detail: str = "Error with camera service."):
        super().__init__(status_code=500, detail=detail)

class AIError(AppException):
    """Exception raised for AI service errors."""
    def __init__(self, detail: str = "An AI service error occurred."):
        super().__init__(status_code=500, detail=detail)

class InvalidFileTypeError(AppException):
    """Exception raised for invalid file types."""
    def __init__(self, detail: str = "Invalid file type."):
        super().__init__(status_code=400, detail=detail)

class InvalidAPIKeyError(AppException):
    """Exception raised for invalid API keys."""
    def __init__(self, detail: str = "Invalid API key."):
        super().__init__(status_code=401, detail=detail)

class RateLimitError(AppException):
    """Exception raised when rate limits are exceeded."""
    def __init__(self, detail: str = "Rate limit exceeded."):
        super().__init__(status_code=429, detail=detail)

class APIResponseError(AppException):
    """Exception raised for errors in the API response."""
    def __init__(self, detail: str = "Error in API response."):
        super().__init__(status_code=500, detail=detail)