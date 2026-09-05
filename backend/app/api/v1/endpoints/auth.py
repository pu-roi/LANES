from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.database import get_db

from app.core.limiter import limiter

router = APIRouter()


@router.post("/login/access-token", response_model=schemas.Token)
@limiter.limit("5/minute")
def login_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    client_ip = request.client.host if request.client else None
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user:
        user = crud.get_user_by_email(db, email=form_data.username)
        
    if not user:
        crud.create_audit_log(
            db,
            audit_in=schemas.AuditLogCreate(
                admin_id=None,
                action_type="LOGIN_FAILURE",
                target_table="users",
                target_id=None,
                metadata_json={
                    "attempted_username": form_data.username,
                    "reason": "Incorrect username"
                },
                ip_address=client_ip
            )
        )
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    if not security.verify_password(form_data.password, user.hashed_password):
        crud.create_audit_log(
            db,
            audit_in=schemas.AuditLogCreate(
                admin_id=None,
                action_type="LOGIN_FAILURE",
                target_table="users",
                target_id=None,
                metadata_json={
                    "attempted_username": form_data.username,
                    "reason": "Incorrect password"
                },
                ip_address=client_ip
            )
        )
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    if not user.is_active:
        if datetime.utcnow() > user.created_at + timedelta(minutes=10):
            crud.hard_delete_user(db, user.id)
            raise HTTPException(status_code=400, detail="Registration expired. Please register again.")
            
        crud.create_audit_log(
            db,
            audit_in=schemas.AuditLogCreate(
                admin_id=user.id,
                action_type="LOGIN_FAILURE",
                target_table="users",
                target_id=user.id,
                metadata_json={
                    "attempted_username": form_data.username,
                    "reason": "Inactive account"
                },
                ip_address=client_ip
            )
        )
        raise HTTPException(status_code=403, detail={"code": "UNVERIFIED_ACCOUNT", "email": user.email})
    
    if user.role.name != "Commuter":
        crud.create_audit_log(
            db,
            audit_in=schemas.AuditLogCreate(
                admin_id=user.id,
                action_type="LOGIN_SUCCESS",
                target_table="users",
                target_id=user.id,
                metadata_json={
                    "username": user.username,
                    "role": user.role.name
                },
                ip_address=client_ip
            )
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            {"sub": str(user.id)}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/test-token", response_model=schemas.UserResponse)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user


from app.schemas.auth import RegistrationRequest, OTPVerificationRequest, OTPResendRequest, SignupOTPRequest
from app.services.auth_service import generate_and_send_otp, validate_otp
from app.crud.user import create_user_with_profile
from app.crud import otp as crud_otp

@router.post("/request-signup-otp")
@limiter.limit("5/minute")
async def request_signup_otp(
    request: Request,
    payload: SignupOTPRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Sends an OTP to the given email for signup verification.
    Enforces progressive cooldown tiers (1m, 3m, 5m).
    """
    existing_email = crud.get_user_by_email(db, email=payload.email)
    if existing_email:
        if existing_email.is_active:
            raise HTTPException(status_code=400, detail="Email already registered")

    sent, err, cooldown_seconds = await generate_and_send_otp(db, email=payload.email)
    if not sent:
        # If the failure is due to cooldown or lockout
        if "Please wait" in err:
            raise HTTPException(
                status_code=429, 
                detail=err,
                headers={"Retry-After": str(cooldown_seconds)}
            )
        raise HTTPException(
            status_code=500, 
            detail=f"Email delivery failed: {err or 'Please check Brevo configuration'}"
        )
    return {
        "msg": "OTP sent successfully",
        "cooldown_seconds": cooldown_seconds
    }


@router.post("/verify-signup-otp")
@limiter.limit("10/minute")
def verify_signup_otp(
    request: Request,
    payload: OTPVerificationRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verifies the OTP code for signup with attempt throttling and sliding grace window.
    """
    result = validate_otp(db, email=payload.email, plain_otp=payload.otp_code)
    
    if result["status"] == "SUCCESS":
        return {"msg": result["message"]}
    elif result["status"] == "LOCKED":
        raise HTTPException(status_code=429, detail=result["message"])
    elif result["status"] == "EXPIRED":
        raise HTTPException(status_code=410, detail=result["message"])
    else:
        raise HTTPException(status_code=400, detail=result["message"])


@router.post("/register", response_model=schemas.UserResponse)
@limiter.limit("3/minute")
async def register(
    request: Request,
    payload: RegistrationRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Registers a new user, creates profile and address. Requires email to be pre-verified.
    """
    existing_username = crud.get_user_by_username(db, username=payload.user.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    existing_email = crud.get_user_by_email(db, email=payload.user.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Verify that the email was actually OTP verified recently
    if not crud_otp.is_email_verified(db, payload.user.email):
        raise HTTPException(status_code=403, detail="Email not verified or verification expired")

    payload.user.is_active = True
    
    try:
        new_user = create_user_with_profile(
            db, 
            user_data=payload.user, 
            profile_data=payload.profile, 
            address_data=payload.address
        )
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

    # Eagerly load the role relationship so UserResponse serialization works
    db.refresh(new_user)
    _ = new_user.role  # Force-load lazy relationship within the session

    # Delete the OTP record so it can't be reused for another account creation
    crud_otp.delete_otp(db, payload.user.email)

    return new_user

@router.post("/verify-otp")
@limiter.limit("5/minute")
def verify_otp(
    request: Request,
    payload: OTPVerificationRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verifies the OTP code. Activates user and returns JWT token if successful.
    """
    user = crud.get_user_by_email(db, email=payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.is_active:
        raise HTTPException(status_code=400, detail="User is already verified")
        
    is_valid = validate_otp(db, email=payload.email, plain_otp=payload.otp_code)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    crud.update_user_status(db, user_id=user.id, is_active=True)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            {"sub": str(user.id)}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/resend-otp")
@limiter.limit("2/minute")
async def resend_otp(
    request: Request,
    payload: OTPResendRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Resends an OTP to the given email if the user exists and is not active.
    """
    user = crud.get_user_by_email(db, email=payload.email)
    if not user:
        return {"msg": "If the email is registered, an OTP has been sent."}
        
    if user.is_active:
        return {"msg": "User is already verified"}
        
    await generate_and_send_otp(db, email=payload.email)
    return {"msg": "OTP resent successfully"}
