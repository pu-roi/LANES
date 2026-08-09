from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.otp import OTPVerification
from app.schemas.otp import OTPVerificationCreate

def create_otp(db: Session, otp_in: OTPVerificationCreate) -> OTPVerification:
    # Delete any existing active OTP for this email
    db.query(OTPVerification).filter(OTPVerification.email == otp_in.email).delete()
    
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
    return db_otp


def get_latest_otp(db: Session, email: str) -> Optional[OTPVerification]:
    return db.query(OTPVerification).filter(
        OTPVerification.email == email
    ).order_by(OTPVerification.created_at.desc()).first()


def increment_otp_attempts(db: Session, otp_id: int) -> OTPVerification:
    otp = db.query(OTPVerification).filter(OTPVerification.id == otp_id).first()
    if otp:
        otp.attempts += 1
        db.commit()
        db.refresh(otp)
    return otp


def mark_otp_verified(db: Session, otp_id: int) -> OTPVerification:
    otp = db.query(OTPVerification).filter(OTPVerification.id == otp_id).first()
    if otp:
        otp.is_verified = True
        db.commit()
        db.refresh(otp)
    return otp


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
