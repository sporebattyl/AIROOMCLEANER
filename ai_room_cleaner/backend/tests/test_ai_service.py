import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import base64
from backend.services.ai_service import AIService
from backend.core.exceptions import AIError, ConfigError

@pytest.mark.asyncio
async def test_analyze_room_for_mess_success(ai_service, mock_settings):
    """Test successful room analysis."""
    # Create test image data
    test_image = base64.b64encode(b"fake_image_data").decode()
    
    with patch('backend.services.ai_service.resize_image_with_vips') as mock_resize, \
         patch.object(ai_service, '_analyze_with_gemini') as mock_analyze:
        
        mock_resize.return_value = b"resized_image_data"
        mock_analyze.return_value = [
            {"mess": "clothes on floor", "reason": "untidy appearance"}
        ]
        
        result = await ai_service.analyze_room_for_mess(test_image)
        
        assert len(result) == 1
        assert result[0]["mess"] == "clothes on floor"
        mock_resize.assert_called_once()
        mock_analyze.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_room_invalid_base64(ai_service):
    """Test handling of invalid base64 data."""
    with pytest.raises(AIError, match="Invalid base64 image data"):
        await ai_service.analyze_room_for_mess("invalid_base64!")

@pytest.mark.asyncio
async def test_analyze_room_empty_image(ai_service):
    """Test handling of empty image data."""
    empty_image = base64.b64encode(b"").decode()
    
    with pytest.raises(AIError, match="Decoded image data is empty"):
        await ai_service.analyze_room_for_mess(empty_image)