import httpx
import base64
from pathlib import Path
from app.core.config import settings

def get_logo_url() -> str:
    # Use direct GitHub raw CDN link to the official logo so all mail clients render it without any download attachments
    return "https://raw.githubusercontent.com/roicambe/LANES/main/frontend/public/lanes-logo/lanes-logo.png"


async def send_otp_email_async(to_email: str, otp_code: str) -> tuple[bool, str]:
    """
    Sends an OTP email using Brevo REST API with clean hosted branding (no attachments).
    Returns (success, error_message)
    """
    if not settings.BREVO_SMTP_KEY:
        print(f"WARN: Brevo API Key not set. Simulating OTP {otp_code} to {to_email}")
        return True, ""

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_SMTP_KEY,
        "content-type": "application/json"
    }

    logo_url = get_logo_url()

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify your email</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 40px 16px;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 540px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 24px rgba(15, 23, 42, 0.06); border: 1px solid #e2e8f0; overflow: hidden; margin: 0 auto;">
            <!-- Brand Header / Seal -->
            <tr>
                <td style="padding: 40px 32px 24px 32px; text-align: center; background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); border-bottom: 1px solid #f1f5f9;">
                    <img 
                        src="{logo_url}" 
                        alt="LANES" 
                        width="160"
                        style="width: 160px; max-width: 100%; height: auto; display: inline-block; margin: 0 auto; border: 0; outline: none; text-decoration: none;" 
                    />
                </td>
            </tr>
            <!-- Main Content -->
            <tr>
                <td style="padding: 36px 36px 32px 36px;">
                    <h1 style="color: #0f172a; font-size: 22px; font-weight: 700; margin: 0 0 12px 0; text-align: center; letter-spacing: -0.3px;">
                        Verify your email address
                    </h1>
                    <p style="color: #64748b; font-size: 15px; line-height: 1.6; margin: 0 0 28px 0; text-align: center;">
                        Welcome to <strong>LANES</strong>! Please enter the single-use verification code below to activate your account.
                    </p>
                    
                    <!-- OTP Code Badge -->
                    <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 28px;">
                        <span style="font-family: 'SF Mono', Consolas, Monaco, monospace; font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #2563eb; display: block; margin-left: 8px;">
                            {otp_code}
                        </span>
                    </div>
                    
                    <p style="color: #94a3b8; font-size: 13px; line-height: 1.5; margin: 0 0 28px 0; text-align: center;">
                        This code will expire in <strong style="color: #64748b;">5 minutes</strong>.<br>If you did not request this verification, please safely ignore this email.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 0 0 24px 0;">
                    
                    <table align="center" border="0" cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                        <tr>
                            <td style="color: #64748b; font-size: 13px; text-align: center; line-height: 1.4;">
                                Stay safe on the road,<br>
                                <strong style="color: #0f172a;">The LANES Team</strong>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        
        <!-- Footer -->
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 540px; margin: 20px auto 0 auto;">
            <tr>
                <td style="color: #94a3b8; font-size: 12px; text-align: center; line-height: 1.5;">
                    &copy; 2026 LANES — Localised Alternative Navigation for Environs under Submersion.<br>
                    All rights reserved.
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    payload: dict = {
        "sender": {"name": "LANES", "email": "roicambe02@gmail.com"},
        "to": [{"email": to_email}],
        "subject": "Your LANES Account Verification Code",
        "htmlContent": html_content
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            return True, ""
        except httpx.HTTPStatusError as e:
            err_msg = f"Brevo HTTP {e.response.status_code}: {e.response.text}"
            print(f"Error sending email via Brevo API: {err_msg}")
            return False, err_msg
        except Exception as e:
            err_msg = f"Brevo Error: {str(e)}"
            print(f"Error sending email via Brevo API: {err_msg}")
            return False, err_msg

