try:
    import pyvips
    VIPS_AVAILABLE = True
except (ImportError, OSError) as e:
    pyvips = None
    VIPS_AVAILABLE = False
    VIPS_ERROR = str(e)

import hashlib
from backend.core.config import Settings
from loguru import logger
from backend.core.exceptions import ImageProcessingError
from cachetools import TTLCache

# In-memory cache for resized images (100 items, 1-hour TTL)
cache = TTLCache(maxsize=100, ttl=3600)

def configure_pyvips(settings: Settings):
    """Configures pyvips settings based on application configuration."""
    if not VIPS_AVAILABLE:
        logger.warning(f"pyvips not available, skipping configuration. Error: {VIPS_ERROR}")
        return
    try:
        if VIPS_AVAILABLE:
            pyvips.cache_set_max(settings.vips_cache_max)
            logger.info(f"pyvips configured with cache_max={settings.vips_cache_max}")
    except Exception as e:
        logger.error(f"Failed to configure pyvips: {e}")
        raise ImageProcessingError(f"Failed to configure image processing: {str(e)}")

def resize_image_with_vips(image_bytes: bytes, settings: Settings) -> bytes:
    """
    Resizes an image using pyvips with memory-saving strategies and error handling.
    """
    # Generate a hash of the image content to use as a cache key
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    if image_hash in cache:
        logger.info(f"Returning cached image for hash: {image_hash}")
        return cache[image_hash]

    if not VIPS_AVAILABLE:
        logger.warning(f"pyvips not available, returning original image bytes. Error: {VIPS_ERROR}")
        return image_bytes

    if not image_bytes:
        raise ImageProcessingError("Empty image data provided")
    
    try:
        # Load image with format detection
        if VIPS_AVAILABLE:
            image = pyvips.Image.new_from_buffer(image_bytes, "")
        
        # Validate image properties
        if image.width <= 0 or image.height <= 0:
            raise ImageProcessingError("Invalid image dimensions")
        
        if image.bands not in [1, 3, 4]:  # Grayscale, RGB, or RGBA
            raise ImageProcessingError(f"Unsupported image format with {image.bands} bands")
        
        logger.info(f"Processing image: {image.width}x{image.height}, {image.bands} bands")
        
        # Convert to RGB if necessary (for JPEG output)
        if image.bands == 4:
            # Remove alpha channel by compositing over white background
            if VIPS_AVAILABLE:
                white_bg = pyvips.Image.new_from_array([[255, 255, 255]], scale=1, offset=0)
            white_bg = white_bg.embed(0, 0, image.width, image.height, extend='copy')
            image = image.composite2(white_bg, 'over')
        elif image.bands == 1:
            # Convert grayscale to RGB
            image = image.colourspace('srgb')
        
        original_size = max(image.width, image.height)
        
        # Aggressive downsampling for high-risk images
        if (image.width > settings.high_risk_dimension_threshold or
            image.height > settings.high_risk_dimension_threshold):
            downsample_factor = original_size / settings.high_risk_dimension_threshold
            logger.warning(f"High-risk image detected. Aggressively downsampling by factor {downsample_factor:.2f}")
            image = image.resize(1 / downsample_factor, kernel='lanczos3')

        # Standard resizing based on max_dimension
        current_max = max(image.width, image.height)
        if current_max > settings.MAX_IMAGE_DIMENSION:
            scale = settings.MAX_IMAGE_DIMENSION / current_max
            logger.info(f"Resizing image by scale factor {scale:.2f}")
            image = image.resize(scale, kernel='lanczos3')
        
        # Output as JPEG with quality control
        output_bytes = image.write_to_buffer(".jpg[Q=85,optimize=true,interlace=true]")
        
        logger.info(f"Image processed: {len(image_bytes)} -> {len(output_bytes)} bytes")
        cache[image_hash] = output_bytes
        return output_bytes
        
    except Exception as e:
        logger.error(f"pyvips error during image processing: {e}")
        raise ImageProcessingError(f"Image processing failed: {str(e)}")