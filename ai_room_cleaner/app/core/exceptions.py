class AIProviderError(Exception):
    """Custom exception for AI provider errors."""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(self.detail)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(self.detail)
