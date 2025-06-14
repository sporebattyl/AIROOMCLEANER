class AppException(Exception):
    """Base application exception."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.detail)

class AIError(AppException):
    """Custom exception for AI service errors."""
    def __init__(self, detail: str = "AI service error."):
        super().__init__(status_code=500, detail=detail)

class CameraError(AppException):
    """Custom exception for camera service errors."""
    def __init__(self, detail: str = "Camera service error."):
        super().__init__(status_code=500, detail=detail)

class ConfigError(AppException):
    """Custom exception for configuration errors."""
    def __init__(self, detail: str = "Configuration error."):
        super().__init__(status_code=500, detail=detail)
class ImageProcessingError(AppException):
    """Custom exception for image processing errors."""
    def __init__(self, detail: str = "Image processing error."):
        super().__init__(status_code=422, detail=detail)