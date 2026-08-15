from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.otp import OTPVerification
from app.schemas.otp import OTPVerificationCreate

COOLDOWN_TIERS = [60, 180, 300]  # 1 min -> 3 mins -> 5 mins

def get_active_otps(db: Session, email: str) -> List[OTPVerification]:
    """Returns all active, unverified, unexpired OTPs for this email, newest first."""
    now = datetime.utcnow()
    return db.query(OTPVerification).filter(
        OTPVerification.email == email,
        OTPVerification.is_verified == False,
        OTPVerification.expires_at > now
    ).order_by(OTPVerification.created_at.desc()).all()


def check_resend_eligibility(db: Session, email: str) -> tuple[bool, int, int]:
    """
    Checks if a new OTP can be requested for this email.
    Returns: (is_eligible, wait_seconds_remaining, next_cooldown_duration)
    """
    now = datetime.utcnow()
    active_otps = get_active_otps(db, email)
    
    # Check if locked out from too many failed attempts (>= 5 attempts across recent codes)
    recent_attempts = sum(o.attempts for o in active_otps)
    if recent_attempts >= 5:
        # Check time since last attempt or newest OTP
        if active_otps:
            lockout_expiry = active_otps[0].created_at + timedelta(minutes=5)
            if now < lockout_expiry:
                remaining_lockout = int((lockout_expiry - now).total_seconds())
                return False, remaining_lockout, 300
    
    if not active_otps:
        return True, 0, COOLDOWN_TIERS[0]
    
    latest_otp = active_otps[0]
    resend_count = len(active_otps)  # 1 means 1 previous code exists, next is 2nd tier
    
    tier_idx = min(resend_count - 1, len(COOLDOWN_TIERS) - 1)
    cooldown_required = COOLDOWN_TIERS[tier_idx]
    
    seconds_passed = (now - latest_otp.created_at).total_seconds()
    if seconds_passed < cooldown_required:
        wait_remaining = int(cooldown_required - seconds_passed)
        return False, wait_remaining, cooldown_required
    
    # Next cooldown tier for the code about to be created
    next_tier_idx = min(resend_count, len(COOLDOWN_TIERS) - 1)
    return True, 0, COOLDOWN_TIERS[next_tier_idx]


def create_otp(db: Session, otp_in: OTPVerificationCreate) -> tuple[OTPVerification, int]:
    """
    Stores an OTP while retaining up to 3 valid recent codes for network latency grace period.
    Purges older codes beyond the 3-code grace window.
    Returns (db_otp, next_cooldown_seconds)
    """
    now = datetime.utcnow()
    # Delete expired or verified OTPs
    db.query(OTPVerification).filter(
        OTPVerification.email == otp_in.email,
        (OTPVerification.expires_at <= now) | (OTPVerification.is_verified == True)
    ).delete()
    
    # Get remaining active codes
    existing_active = db.query(OTPVerification).filter(
        OTPVerification.email == otp_in.email
    ).order_by(OTPVerification.created_at.desc()).all()
    
    # If more than 2 already exist, delete the oldest so total never exceeds 3
    if len(existing_active) >= 2:
        for old_otp in existing_active[1:]:
            db.delete(old_otp)
    
    db_otp = OTPVerification(
        email=otp_in.email,
        otp_code=otp_in.otp_code,
        expires_at=otp_in.expires_at,
        attempts=0,
        is_verified=False
    )
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)
    
    # Determine cooldown for the user
    total_active = len(get_active_otps(db, otp_in.email))
    next_tier_idx = min(total_active - 1, len(COOLDOWN_TIERS) - 1)
    return db_otp, COOLDOWN_TIERS[next_tier_idx]


def get_latest_otp(db: Session, email: str) -> Optional[OTPVerification]:
    return db.query(OTPVerification).filter(
        OTPVerification.email == email
    ).order_by(OTPVerification.created_at.desc()).first()


def increment_otp_attempts(db: Session, email: str) -> int:
    """Increments attempt count on active OTPs for this email and returns total failed attempts."""
    active_otps = get_active_otps(db, email)
    total_attempts = 0
    for otp in active_otps:
        otp.attempts += 1
        total_attempts += otp.attempts
    db.commit()
    return total_attempts


def mark_all_otps_verified(db: Session, email: str) -> None:
    """Marks verified and invalidates other pending OTPs for the email."""
    now = datetime.utcnow()
    active_otps = get_active_otps(db, email)
    for otp in active_otps:
        otp.is_verified = True
    db.commit()


def delete_otp(db: Session, email: str) -> None:
    db.query(OTPVerification).filter(OTPVerification.email == email).delete()
    db.commit()


def is_email_verified(db: Session, email: str) -> bool:
    """Checks if the email has a verified OTP within the last 30 minutes."""
    cutoff = datetime.utcnow() - timedelta(minutes=30)
    otp = db.query(OTPVerification).filter(
        OTPVerification.email == email,
        OTPVerification.is_verified == True,
        OTPVerification.created_at >= cutoff
    ).order_by(OTPVerification.created_at.desc()).first()
    return otp is not None
