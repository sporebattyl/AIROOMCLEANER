import pyvips
from backend.core.config import Settings
from loguru import logger

def configure_pyvips(settings: Settings):
    """Configures pyvips settings based on application configuration."""
    pyvips.cache_set_max_mem(settings.vips_cache_max * 1024 * 1024)
    logger.info(f"pyvips configured with cache_max_mem={settings.vips_cache_max}MB")

def resize_image_with_vips(image_bytes: bytes, settings: Settings) -> bytes:
    """
    Resizes an image using pyvips with memory-saving strategies.
    - Applies aggressive downsampling for very large images.
    - Uses the configured max dimension for standard resizing.
    """
    image = pyvips.Image.new_from_buffer(image_bytes, "")

    # Aggressive downsampling for high-risk images
    if image.width > settings.high_risk_dimension_threshold or image.height > settings.high_risk_dimension_threshold:
        downsample_factor = max(image.width, image.height) / settings.high_risk_dimension_threshold
        logger.warning(f"High-risk image detected. Aggressively downsampling by a factor of {downsample_factor:.2f}.")
        image = image.resize(1 / downsample_factor)

    # Standard resizing based on max_dimension
    if image.width > settings.max_image_dimension or image.height > settings.max_image_dimension:
        scale = settings.max_image_dimension / max(image.width, image.height)
        image = image.resize(scale)
    
    return image.write_to_buffer(".jpg[Q=85]")