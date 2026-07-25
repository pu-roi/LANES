import httpx
import base64
from pathlib import Path
from app.core.config import settings

def get_logo_url() -> str:
    # Use the Cloudinary hosted public URL so email clients like Gmail do not block the image
    return "https://res.cloudinary.com/r8dbejb2/image/upload/v1784998835/lanes_logo_email.png"


async def send_otp_email_async(to_email: str, otp_code: str) -> bool:
    """
    Sends an OTP email using Brevo REST API.
    """
    if not settings.BREVO_SMTP_KEY:
        print(f"WARN: Brevo API Key not set. Simulating OTP {otp_code} to {to_email}")
        return True

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_SMTP_KEY,
        "content-type": "application/json"
    }
    
    logo_src = get_logo_url()

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: 'Inter', Helvetica, Arial, sans-serif; background-color: #f4f7f6; margin: 0; padding: 40px 0;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); overflow: hidden; margin: auto;">
            <tr>
                <td style="padding: 40px 40px 20px 40px; text-align: center; background-color: #ffffff;">
                    <img src="{logo_src}" alt="LANES Logo" style="max-width: 140px; margin-bottom: 10px;"/>
                </td>
            </tr>
            <tr>
                <td style="padding: 0 40px 30px 40px;">
                    <h1 style="color: #0f172a; font-size: 24px; font-weight: 700; margin: 0 0 20px 0; text-align: center;">Verify your email address</h1>
                    <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0; text-align: center;">
                        Welcome to LANES! Please enter the code below to verify your email address and complete your registration.
                    </p>
                    
                    <div style="background-color: #f1f5f9; border-radius: 8px; padding: 24px; text-align: center; margin-bottom: 30px;">
                        <span style="font-family: monospace; font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #2563eb;">{otp_code}</span>
                    </div>
                    
                    <p style="color: #64748b; font-size: 14px; line-height: 1.5; margin: 0 0 30px 0; text-align: center;">
                        This code will expire in <strong>10 minutes</strong>.<br>If you didn't request this email, you can safely ignore it.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 0 0 30px 0;">
                    
                    <p style="color: #94a3b8; font-size: 13px; margin: 0; text-align: center;">
                        Stay safe on the road,<br><strong>The LANES Team</strong>
                    </p>
                </td>
            </tr>
        </table>
        <p style="color: #94a3b8; font-size: 12px; text-align: center; margin-top: 20px;">
            &copy; 2026 LANES. All rights reserved.
        </p>
    </body>
    </html>
    """

    payload = {
        "sender": {"name": "LANES", "email": "roicambe02@gmail.com"},
        "to": [{"email": to_email}],
        "subject": "Your LANES Account Verification Code",
        "htmlContent": html_content
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            print(f"Error sending email via Brevo API: HTTP {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            print(f"Error sending email via Brevo API: {e}")
            return False

