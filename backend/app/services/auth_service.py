import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.crud import otp as crud_otp
from app.schemas.otp import OTPVerificationCreate
from app.services.email_service import send_otp_email_async
import bcrypt

def get_otp_hash(otp_code: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(otp_code.encode('utf-8'), salt).decode('utf-8')

def verify_otp_hash(plain_otp: str, hashed_otp: str) -> bool:
    try:
        return bcrypt.checkpw(plain_otp.encode('utf-8'), hashed_otp.encode('utf-8'))
    except ValueError:
        return False

def generate_otp_code() -> str:
    # Generate 6 digit numeric code
    return str(secrets.randbelow(1000000)).zfill(6)


async def generate_and_send_otp(db: Session, email: str) -> tuple[bool, str, int]:
    """
    Generate a 6-digit OTP, hash it, store it in the database, and send it to the user.
    Checks progressive cooldown eligibility before generating.
    Returns (success, error_or_message, next_cooldown_seconds)
    """
    eligible, wait_seconds, cooldown_seconds = crud_otp.check_resend_eligibility(db, email)
    if not eligible:
        if wait_seconds >= 60:
            minutes = (wait_seconds + 59) // 60
            err_msg = f"Please wait {minutes} minute(s) before requesting another code. Please check your spam folder."
        else:
            err_msg = f"Please wait {wait_seconds} second(s) before requesting another code."
        return False, err_msg, wait_seconds

    code = generate_otp_code()
    hashed_code = get_otp_hash(code)
    
    # 5 minutes expiry per user requirement
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    otp_in = OTPVerificationCreate(
        email=email,
        otp_code=hashed_code,
        expires_at=expires_at
    )
    
    _, next_cooldown = crud_otp.create_otp(db, otp_in)
    
    # Send via email service
    success, err = await send_otp_email_async(to_email=email, otp_code=code)
    if not success:
        return False, err, next_cooldown
        
    return True, "", next_cooldown


def validate_otp(db: Session, email: str, plain_otp: str) -> dict:
    """
    Validates an OTP against all active unexpired codes for the email (grace window).
    Returns dict: {"status": "SUCCESS"|"EXPIRED"|"INVALID"|"LOCKED", "message": str, "attempts_left": int}
    """
    now = datetime.utcnow()
    active_otps = crud_otp.get_active_otps(db, email)
    
    if not active_otps:
        # Check if there is an expired OTP
        latest = crud_otp.get_latest_otp(db, email)
        if latest and not latest.is_verified:
            return {
                "status": "EXPIRED",
                "message": "Your verification code has expired. Please click 'Resend Code' for a new one.",
                "attempts_left": 0
            }
        return {
            "status": "INVALID",
            "message": "No active verification code found. Please request a new code.",
            "attempts_left": 0
        }
        
    # Check if locked out (5 or more attempts)
    total_attempts = sum(o.attempts for o in active_otps)
    if total_attempts >= 5:
        return {
            "status": "LOCKED",
            "message": "Too many incorrect attempts. Verification is locked for 5 minutes.",
            "attempts_left": 0
        }
        
    # Check if any active valid OTP matches
    for otp_record in active_otps:
        if verify_otp_hash(plain_otp, otp_record.otp_code):
            crud_otp.mark_all_otps_verified(db, email)
            return {
                "status": "SUCCESS",
                "message": "Email verified successfully! Let's complete your profile.",
                "attempts_left": 5
            }
            
    # If none matched, increment attempts across active codes
    new_total_attempts = crud_otp.increment_otp_attempts(db, email)
    remaining_attempts = max(0, 5 - new_total_attempts)
    
    if remaining_attempts == 0:
        return {
            "status": "LOCKED",
            "message": "Too many incorrect attempts. Verification is locked for 5 minutes.",
            "attempts_left": 0
        }
        
    return {
        "status": "INVALID",
        "message": f"Invalid verification code. You have {remaining_attempts} attempt(s) remaining.",
        "attempts_left": remaining_attempts
    }
