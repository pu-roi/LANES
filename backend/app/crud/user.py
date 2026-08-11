
from typing import Optional, List
from sqlalchemy.orm import Session

from app import models, schemas


from app.core.security import get_password_hash


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id, models.User.deleted_at.is_(None)).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username, models.User.deleted_at.is_(None)).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email, models.User.deleted_at.is_(None)).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_pass = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pass,
        role_id=user.role_id,
        is_active=getattr(user, 'is_active', True)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user_with_profile(
    db: Session, 
    user_data: schemas.UserCreate, 
    profile_data: schemas.ProfileCreate, 
    address_data: schemas.AddressCreate
) -> models.User:
    hashed_pass = get_password_hash(user_data.password)
    
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pass,
        role_id=user_data.role_id,
        is_active=getattr(user_data, 'is_active', False)  # Start inactive for OTP flow
    )
    db.add(db_user)
    db.flush()  # To get db_user.id
    
    db_profile = models.Profile(
        user_id=db_user.id,
        **profile_data.model_dump()
    )
    db.add(db_profile)
    db.flush()
    
    db_address = models.Address(
        profile_id=db_profile.id,
        **address_data.model_dump()
    )
    db.add(db_address)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def get_users_filtered(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    archived: bool = False
) -> tuple[List[models.User], int]:
    if archived:
        query = db.query(models.User).filter(models.User.deleted_at.is_not(None))
    else:
        query = db.query(models.User).filter(models.User.deleted_at.is_(None))
    
    if search:
        query = query.filter(
            models.User.username.ilike(f"%{search}%") | 
            models.User.email.ilike(f"%{search}%")
        )
    
    if role and role != "all":
        query = query.join(models.Role).filter(models.Role.name == role)
        
    total = query.count()
    users = query.order_by(models.User.created_at.desc()).offset(skip).limit(limit).all()
    return users, total


def update_user_status(db: Session, user_id: int, is_active: bool) -> Optional[models.User]:
    user = get_user(db, user_id)
    if user:
        user.is_active = is_active
        db.commit()
        db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user(db, user_id)
    if user:
        from datetime import datetime
        user.deleted_at = datetime.utcnow()
        db.commit()
        return True
    return False


def update_user_role(db: Session, user_id: int, role_id: int) -> Optional[models.User]:
    user = get_user(db, user_id)
    if user:
        user.role_id = role_id
        db.commit()
        db.refresh(user)
    return user


def hard_delete_user(db: Session, user_id: int) -> bool:
    """
    Physically removes a user from the database. 
    Useful for wiping out unverified stale accounts.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
