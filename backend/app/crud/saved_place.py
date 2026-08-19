from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.saved_place import SavedPlace
from app.schemas.saved_place import SavedPlaceCreate, SavedPlaceUpdate

def get_saved_places_by_user(db: Session, user_id: int) -> List[SavedPlace]:
    """Retrieve all saved places for a specific user."""
    stmt = select(SavedPlace).where(SavedPlace.user_id == user_id).order_by(SavedPlace.created_at.desc())
    return list(db.execute(stmt).scalars().all())

MAX_SAVED_PLACES = 10

def create_saved_place(db: Session, obj_in: SavedPlaceCreate, user_id: int) -> SavedPlace:
    """Create a new saved place with a maximum cap of 10 places per user."""
    
    # Check current count of saved places for user
    count_stmt = select(func.count(SavedPlace.id)).where(SavedPlace.user_id == user_id)
    current_count = db.execute(count_stmt).scalar() or 0
    
    if current_count >= MAX_SAVED_PLACES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You have reached the maximum limit of {MAX_SAVED_PLACES} saved places. Please remove an existing place to add a new one."
        )
    
    # Construct PostGIS POINT geometry from longitude and latitude
    # Note: Longitude comes first in WKT!
    wkt_point = f"SRID=4326;POINT({obj_in.longitude} {obj_in.latitude})"
    
    db_obj = SavedPlace(
        user_id=user_id,
        name=obj_in.name,
        icon=obj_in.icon,
        address=obj_in.address,
        latitude=obj_in.latitude,
        longitude=obj_in.longitude,
        geometry=wkt_point
    )
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_saved_place(db: Session, place_id: int, user_id: int) -> bool:
    """Delete a saved place if it belongs to the user."""
    stmt = select(SavedPlace).where(
        and_(SavedPlace.id == place_id, SavedPlace.user_id == user_id)
    )
    place = db.execute(stmt).scalar_one_or_none()
    
    if not place:
        return False
        
    db.delete(place)
    db.commit()
    return True
