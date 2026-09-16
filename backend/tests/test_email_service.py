import pytest
from unittest.mock import patch, AsyncMock
import httpx
from app.services.email_service import send_otp_email_async
from app.core.config import settings

@pytest.mark.asyncio
async def test_send_otp_email_resend_success():
    """Verify that send_otp_email_async posts to Resend API with correct headers, sender, and payload."""
    with patch.object(settings, "RESEND_API_KEY", "re_test_key_12345"), \
         patch.object(settings, "RESEND", ""), \
         patch.object(settings, "RESEND_FROM_EMAIL", "Lanes <noreply@navlanes.live>"):
        
        mock_response = httpx.Response(200, json={"id": "msg_test_123"}, request=httpx.Request("POST", "https://api.resend.com/emails"))
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            success, err = await send_otp_email_async(to_email="user@example.com", otp_code="123456")
            
            assert success is True
            assert err == ""
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args.kwargs
            
            assert call_kwargs["headers"]["Authorization"] == "Bearer re_test_key_12345"
            assert call_kwargs["json"]["from"] == "Lanes <noreply@navlanes.live>"
            assert call_kwargs["json"]["to"] == ["user@example.com"]
            assert call_kwargs["json"]["subject"] == "Your LANES Account Verification Code"
            assert "123456" in call_kwargs["json"]["html"]
            assert "Verify your email address" in call_kwargs["json"]["html"]

@pytest.mark.asyncio
async def test_send_otp_email_resend_simulation_when_no_key():
    """Verify that when no API key is configured, delivery is simulated without failing."""
    with patch.object(settings, "RESEND_API_KEY", ""), \
         patch.object(settings, "RESEND", ""):
        
        success, err = await send_otp_email_async(to_email="user@example.com", otp_code="654321")
        assert success is True
        assert err == ""

@pytest.mark.asyncio
async def test_send_otp_email_resend_http_error():
    """Verify that Resend HTTP errors surface the descriptive message."""
    with patch.object(settings, "RESEND_API_KEY", "re_test_key_12345"), \
         patch.object(settings, "RESEND", ""):
        
        mock_response = httpx.Response(
            403, 
            json={"message": "You can only send testing emails to your own email address."}, 
            request=httpx.Request("POST", "https://api.resend.com/emails")
        )
        
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            success, err = await send_otp_email_async(to_email="user@example.com", otp_code="123456")
            assert success is False
            assert "You can only send testing emails to your own email address." in err
