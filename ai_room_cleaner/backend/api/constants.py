"""
Constants for the API endpoints.
"""

# The endpoint for analyzing the room
ANALYZE_ROUTE = "/v1/analyze-room-secure"

# Allowed MIME types for file uploads
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif"}

# Chunk sizes for file reading
MIME_TYPE_CHUNK_SIZE = 2048
FILE_READ_CHUNK_SIZE = 8192
