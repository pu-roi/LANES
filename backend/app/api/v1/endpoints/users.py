from typing import Optional
import re
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.database import get_db
from app.api import deps
from app.models.user import User

router = APIRouter()


@router.get("/check-username")
def check_username_availability(
    username: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(deps.get_current_user_optional)
):
    """
    Check if a username is valid and available (unique).
    """
    if not username or not username.strip():
        return {"available": False, "message": "Username cannot be empty"}
    
    clean = username.strip().lower()
    
    if len(clean) < 3:
        return {"available": False, "message": "Username must be at least 3 characters long"}
    if len(clean) > 30:
        return {"available": False, "message": "Username must not exceed 30 characters"}
    if not re.match(r"^[a-zA-Z0-9._]+$", clean):
        return {"available": False, "message": "Username can only contain alphanumeric characters, underscores, and dots"}
    if clean.startswith((".", "_")) or clean.endswith((".", "_")) or ".." in clean or "__" in clean:
        return {"available": False, "message": "Username cannot start/end with symbols or have consecutive symbols"}

    existing = db.query(User).filter(func.lower(User.username) == clean).first()
    if existing:
        if current_user and existing.id == current_user.id:
            return {"available": True, "message": "This is your current username", "is_current": True}
        return {"available": False, "message": "Username is already taken"}
    
    return {"available": True, "message": "Username is available!"}


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user or administrator.
    """
    # Check if username is taken
    db_user_username = crud.get_user_by_username(db, username=user.username)
    if db_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    # Check if email is taken
    db_user_email = crud.get_user_by_email(db, email=user.email)
    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    return crud.create_user(db=db, user=user)


@router.patch("/me/profile", response_model=schemas.UserResponse)
def update_user_profile(
    profile_in: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update the current user's profile and user details (including username, personal info, address, etc.)
    """
    from app.models.address import Address
    from app.models.profile import Profile
    
    profile = current_user.profile
    if not profile:
        profile = Profile(user_id=current_user.id, first_name=current_user.username, last_name="", display_full_name=True, is_public=True)
        db.add(profile)
        db.flush()
        current_user.profile = profile
        
    update_data = profile_in.model_dump(exclude_unset=True)
    address_data = update_data.pop('address', None)
    username_data = update_data.pop('username', None)

    # If username is being changed
    if username_data is not None:
        clean_username = username_data.strip().lower()
        if clean_username != current_user.username.lower():
            if len(clean_username) < 3:
                raise HTTPException(status_code=400, detail="Username must be at least 3 characters long")
            if len(clean_username) > 30:
                raise HTTPException(status_code=400, detail="Username must not exceed 30 characters")
            if not re.match(r"^[a-zA-Z0-9._]+$", clean_username):
                raise HTTPException(status_code=400, detail="Username can only contain alphanumeric characters, underscores, and dots")
            if clean_username.startswith((".", "_")) or clean_username.endswith((".", "_")) or ".." in clean_username or "__" in clean_username:
                raise HTTPException(status_code=400, detail="Invalid username format")
            
            existing = db.query(User).filter(
                func.lower(User.username) == clean_username,
                User.id != current_user.id
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail="Username is already taken. Please choose another one.")
            
            current_user.username = clean_username
            db.add(current_user)

    for field, value in update_data.items():
        setattr(profile, field, value)
        
    if address_data:
        if profile.address:
            for field, value in address_data.items():
                setattr(profile.address, field, value)
        else:
            new_address = Address(profile_id=profile.id, **address_data)
            db.add(new_address)
            profile.address = new_address

    db.add(profile)
    db.commit()
    db.refresh(profile)
    db.refresh(current_user)
    _ = current_user.role  # Ensure role relationship is loaded
    return current_user



@router.post("/me/avatar", response_model=schemas.ProfileResponse)
def upload_user_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Upload and update the current user's profile avatar image.
    """
    from app.services.cloudinary_service import upload_image
    from app.models.profile import Profile

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image (JPEG, PNG, WebP, etc.).")

    profile = current_user.profile
    if not profile:
        profile = Profile(user_id=current_user.id, first_name=current_user.username, last_name="", display_full_name=True, is_public=True)
        db.add(profile)
        db.flush()
        current_user.profile = profile

    url = upload_image(file)
    if not url:
        raise HTTPException(status_code=500, detail="Failed to upload image to cloud storage.")

    profile.avatar_url = url
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/me/avatar", response_model=schemas.ProfileResponse)
def delete_user_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Remove the current user's profile avatar image.
    """
    from app.models.profile import Profile

    profile = current_user.profile
    if not profile:
        profile = Profile(user_id=current_user.id, first_name=current_user.username, last_name="", display_full_name=True, is_public=True)
        db.add(profile)
        db.flush()
        current_user.profile = profile

    profile.avatar_url = None
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/me", status_code=status.HTTP_200_OK)
def delete_current_user_account(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Self-deactivation / soft deletion of the current user's profile and account.
    Initiates a 30-day grace period before permanent automatic purge.
    """
    from datetime import datetime
    current_user.deleted_at = datetime.utcnow()
    current_user.is_active = False
    db.commit()

    client_ip = request.client.host if request.client else None
    crud.create_audit_log(
        db,
        audit_in=schemas.AuditLogCreate(
            admin_id=current_user.id,
            action_type="USER_SELF_DEACTIVATION",
            target_table="users",
            target_id=current_user.id,
            metadata_json={
                "username": current_user.username,
                "email": current_user.email,
                "grace_period_days": 30
            },
            ip_address=client_ip
        )
    )

    return {
        "message": "Account successfully deactivated. You have a 30-day grace period to log back in before your profile and data are permanently deleted."
    }


from typing import List

@router.get("/me/places", response_model=List[schemas.SavedPlaceResponse])
def get_my_saved_places(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get all saved places for the current user.
    """
    return crud.get_saved_places_by_user(db=db, user_id=current_user.id)

@router.post("/me/places", response_model=schemas.SavedPlaceResponse, status_code=status.HTTP_201_CREATED)
def create_my_saved_place(
    place_in: schemas.SavedPlaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new saved place for the current user.
    """
    return crud.create_saved_place(db=db, obj_in=place_in, user_id=current_user.id)

@router.delete("/me/places/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_saved_place(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete a saved place for the current user.
    """
    deleted = crud.delete_saved_place(db=db, place_id=place_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Saved place not found or not authorized")
    return None

@router.patch("/me/places/{place_id}", response_model=schemas.SavedPlaceResponse)
def update_my_saved_place(
    place_id: int,
    place_in: schemas.SavedPlaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update a saved place (e.g., pinning) for the current user.
    """
    updated_place = crud.update_saved_place(db=db, place_id=place_id, user_id=current_user.id, obj_in=place_in)
    if not updated_place:
        raise HTTPException(status_code=404, detail="Saved place not found or not authorized")
    return updated_place


@router.post("/me/password/request-otp")
async def request_password_change_otp(
    payload: schemas.PasswordChangeOtpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Validates current password and dispatches a 6-digit OTP to the user's email for password change.
    """
    from app.core import security
    from app.services import auth_service

    if not security.verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    success, err_msg, cooldown = await auth_service.generate_and_send_password_change_otp(
        db, email=current_user.email
    )
    if not success:
        raise HTTPException(status_code=400, detail=err_msg or "Failed to send verification code")

    return {
        "message": f"Verification code sent to {current_user.email}",
        "cooldown_seconds": cooldown,
        "email": current_user.email
    }


@router.put("/me/password")
def change_my_password(
    payload: schemas.PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Change current user's password with current password and email OTP verification.
    """
    from app.core import security
    from app.services import auth_service

    if not security.verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    if not payload.otp_code or len(payload.otp_code.strip()) != 6:
        raise HTTPException(status_code=400, detail="Please enter a valid 6-digit verification code")

    otp_validation = auth_service.validate_otp(db, email=current_user.email, plain_otp=payload.otp_code.strip())
    if otp_validation.get("status") != "SUCCESS":
        raise HTTPException(status_code=400, detail=otp_validation.get("message", "Invalid or expired verification code"))

    pwd = payload.new_password
    if len(pwd) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    if " " in pwd:
        raise HTTPException(status_code=400, detail="Password cannot contain spaces")
    if not re.search(r"[a-z]", pwd) or not re.search(r"[A-Z]", pwd):
        raise HTTPException(status_code=400, detail="Password must contain both uppercase and lowercase letters")
    if not re.search(r"\d", pwd) or not re.search(r"[^a-zA-Z\d\s]", pwd):
        raise HTTPException(status_code=400, detail="Password must contain at least one number and one special character")

    crud.update_user_password(db, user_id=current_user.id, new_password=pwd)
    return {"message": "Password updated successfully"}


