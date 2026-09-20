import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.crud import otp as crud_otp
from app.schemas.otp import OTPVerificationCreate
from app.services.email_service import send_otp_email_async, send_password_reset_email_async, send_password_change_otp_email_async
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


async def generate_and_send_password_reset_otp(db: Session, email: str) -> tuple[bool, str, int]:
    """
    Generate a 6-digit OTP for password reset, hash it, store it in the database,
    and send it via the password reset email template.
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
    
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    otp_in = OTPVerificationCreate(
        email=email,
        otp_code=hashed_code,
        expires_at=expires_at
    )
    
    _, next_cooldown = crud_otp.create_otp(db, otp_in)
    
    success, err = await send_password_reset_email_async(to_email=email, otp_code=code)
    if not success:
        return False, err, next_cooldown
        
    return True, "", next_cooldown


async def generate_and_send_password_change_otp(db: Session, email: str) -> tuple[bool, str, int]:
    """
    Generate a 6-digit OTP for confirming a password change, hash it, store it in the database,
    and send it via the password change email template.
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
    
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    otp_in = OTPVerificationCreate(
        email=email,
        otp_code=hashed_code,
        expires_at=expires_at
    )
    
    _, next_cooldown = crud_otp.create_otp(db, otp_in)
    
    success, err = await send_password_change_otp_email_async(to_email=email, otp_code=code)
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


import re
from fastapi import HTTPException
from app import crud, models, schemas
from app.core.config import settings
from app.core.security import get_password_hash
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
import httpx


def verify_google_token(credential: str | None = None, access_token: str | None = None) -> dict:
    """
    Validates a Google ID Token (credential) or Google OAuth2 access token.
    Extracts verified user profile information.
    """
    if not credential and not access_token:
        raise HTTPException(status_code=400, detail="Google authentication token is required")

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google authentication is not configured on the backend. Please check GOOGLE_CLIENT_ID."
        )

    # 1. Verify via Google ID Token (Credential)
    if credential:
        try:
            id_info = google_id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
        except ValueError as e:
            raise HTTPException(status_code=401, detail=f"Invalid or expired Google token: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Google token verification failed: {str(e)}")

        if id_info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            raise HTTPException(status_code=401, detail="Invalid Google token issuer")

        email = id_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google account")
        if not id_info.get("email_verified", False):
            raise HTTPException(status_code=400, detail="Your Google email address is not verified")

        return {
            "email": email.lower().strip(),
            "name": id_info.get("name", ""),
            "given_name": id_info.get("given_name", ""),
            "family_name": id_info.get("family_name", ""),
            "picture": id_info.get("picture", None),
            "sub": id_info.get("sub", "")
        }

    # 2. Verify via Google OAuth2 Access Token
    if access_token:
        try:
            # Check tokeninfo for audience/client_id verification
            tokeninfo_res = httpx.get(
                f"https://oauth2.googleapis.com/tokeninfo?access_token={access_token}",
                timeout=10.0
            )
            if tokeninfo_res.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google access token")

            tokeninfo = tokeninfo_res.json()
            # Verify aud or azp matches our GOOGLE_CLIENT_ID
            token_aud = tokeninfo.get("aud") or tokeninfo.get("azp")
            if token_aud != settings.GOOGLE_CLIENT_ID:
                raise HTTPException(status_code=401, detail="Google token was not issued for this application")

            # Fetch profile information from Google userinfo endpoint
            userinfo_res = httpx.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0
            )
            if userinfo_res.status_code != 200:
                raise HTTPException(status_code=401, detail="Failed to retrieve Google user information")

            userinfo = userinfo_res.json()
            email = userinfo.get("email")
            if not email or not userinfo.get("email_verified", False):
                raise HTTPException(status_code=400, detail="Google account has unverified or missing email")

            return {
                "email": email.lower().strip(),
                "name": userinfo.get("name", ""),
                "given_name": userinfo.get("given_name", ""),
                "family_name": userinfo.get("family_name", ""),
                "picture": userinfo.get("picture", None),
                "sub": userinfo.get("sub", "")
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Google OAuth verification failed: {str(e)}")

    raise HTTPException(status_code=400, detail="Invalid Google authentication request")


def authenticate_or_register_google_user(
    db: Session,
    google_info: dict,
    mode: str = "login",
    user_data: schemas.UserCreate | None = None,
    profile_data: schemas.ProfileCreate | None = None,
    address_data: schemas.AddressCreate | None = None,
    client_ip: str | None = None
) -> tuple[models.User, bool]:
    """
    Handles Google OAuth authentication:
    - If mode == 'login': Requires an existing account. If not found, raises 404.
    - If mode == 'register': Creates a new user with verified Google email + profile/address details.
      If the account already exists, safely signs them in.
    Returns (user, is_new_user).
    """
    email = google_info["email"]
    existing_user = crud.get_user_by_email(db, email=email)

    if mode == "login":
        if not existing_user:
            raise HTTPException(
                status_code=404,
                detail="No registered account found with this Google email. Please sign up first."
            )

        if existing_user.deleted_at is not None:
            raise HTTPException(
                status_code=400,
                detail="This account has been deactivated. Please contact administrator support."
            )

        # If user account was unverified/inactive, activate it now since Google proved ownership
        if not existing_user.is_active:
            existing_user.is_active = True
            db.commit()
            db.refresh(existing_user)

        # Update profile avatar if missing and Google provided one
        if existing_user.profile and not existing_user.profile.avatar_url and google_info.get("picture"):
            existing_user.profile.avatar_url = google_info["picture"]
            db.commit()
            db.refresh(existing_user)

        # Log audit entry for login
        crud.create_audit_log(
            db,
            audit_in=schemas.AuditLogCreate(
                admin_id=existing_user.id if getattr(existing_user.role, "name", "") != "Commuter" else None,
                action_type="LOGIN_SUCCESS",
                target_table="users",
                target_id=existing_user.id,
                metadata_json={
                    "provider": "google",
                    "email": existing_user.email,
                    "username": existing_user.username,
                    "role": getattr(existing_user.role, "name", "Commuter")
                },
                ip_address=client_ip
            )
        )

        return existing_user, False

    # mode == "register"
    if existing_user:
        if existing_user.deleted_at is not None:
            raise HTTPException(
                status_code=400,
                detail="This account has been deactivated. Please contact administrator support."
            )
        if not existing_user.is_active:
            existing_user.is_active = True
            db.commit()
            db.refresh(existing_user)
        return existing_user, False

    # New User: Register via Google Account
    # 1. Determine username
    candidate_username = None
    if user_data and user_data.username:
        requested = user_data.username.strip()
        if crud.get_user_by_username(db, username=requested) is None:
            candidate_username = requested

    if not candidate_username:
        raw_prefix = email.split("@")[0].lower()
        clean_base = re.sub(r"[^a-zA-Z0-9._]", "", raw_prefix)[:25]
        if not clean_base or len(clean_base) < 3:
            clean_base = "user"
        candidate_username = clean_base
        counter = 1
        while crud.get_user_by_username(db, username=candidate_username) is not None:
            candidate_username = f"{clean_base[:20]}{counter}"
            counter += 1

    # 2. Secure unusable random password hash
    random_pw = secrets.token_urlsafe(32)
    hashed_pass = get_password_hash(random_pw)

    # 3. Find Commuter role
    commuter_role = db.query(models.Role).filter(models.Role.name == "Commuter").first()
    role_id = user_data.role_id if (user_data and user_data.role_id) else (commuter_role.id if commuter_role else 4)

    new_user = models.User(
        username=candidate_username,
        email=email,
        hashed_password=hashed_pass,
        role_id=role_id,
        is_active=True
    )
    db.add(new_user)
    db.flush()

    # 4. Create Profile (with user-provided info or Google fallback)
    raw_name = (google_info.get("name") or "").strip()
    given_name = (google_info.get("given_name") or "").strip()
    family_name = (google_info.get("family_name") or "").strip()
    if not given_name and raw_name:
        parts = raw_name.split()
        given_name = parts[0]
        family_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    first_name = (profile_data.first_name if profile_data and profile_data.first_name else given_name or candidate_username)[:100]
    last_name = (profile_data.last_name if profile_data and profile_data.last_name else family_name or "")[:100]

    avatar_url = google_info.get("picture") or (profile_data.avatar_url if profile_data else None)

    new_profile = models.Profile(
        user_id=new_user.id,
        first_name=first_name,
        last_name=last_name,
        middle_initial=profile_data.middle_initial if profile_data else None,
        suffix=profile_data.suffix if profile_data else None,
        contact_number=profile_data.contact_number if profile_data else None,
        birthdate=profile_data.birthdate if profile_data else None,
        avatar_url=avatar_url,
        cover_color="#3B82F6",
        is_public=True,
        display_full_name=True
    )
    db.add(new_profile)
    db.flush()

    # 5. Create Address
    if address_data:
        new_address = models.Address(
            profile_id=new_profile.id,
            house_number=address_data.house_number,
            street=address_data.street,
            barangay=address_data.barangay or "",
            city_municipality=address_data.city_municipality or "",
            province=address_data.province or "",
            postal_code=address_data.postal_code,
            country=address_data.country or "Philippines"
        )
    else:
        new_address = models.Address(
            profile_id=new_profile.id,
            barangay="",
            city_municipality="",
            province="",
            country="Philippines"
        )
    db.add(new_address)
    db.commit()
    db.refresh(new_user)
    _ = new_user.role

    # 6. Audit log for new registration
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=None,
            action_type="REGISTER_SUCCESS",
            target_table="users",
            target_id=new_user.id,
            metadata_json={
                "provider": "google",
                "email": new_user.email,
                "username": new_user.username,
                "role": "Commuter"
            },
            ip_address=client_ip
        )
    )

    return new_user, True


