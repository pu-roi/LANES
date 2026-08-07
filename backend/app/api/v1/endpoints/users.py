from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.database import get_db

router = APIRouter()


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

from app.api import deps
from app.models.user import User

@router.patch("/me/profile", response_model=schemas.ProfileResponse)
def update_user_profile(
    profile_in: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update the current user's profile details (e.g. cover color, privacy settings, etc.)
    """
    from app.models.address import Address
    
    profile = current_user.profile
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    update_data = profile_in.model_dump(exclude_unset=True)
    address_data = update_data.pop('address', None)

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
    return profile
