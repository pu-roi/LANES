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

def update_saved_place(db: Session, place_id: int, user_id: int, obj_in: SavedPlaceUpdate) -> Optional[SavedPlace]:
    """Update a saved place and automatically unpin oldest if pinning > 3."""
    stmt = select(SavedPlace).where(
        and_(SavedPlace.id == place_id, SavedPlace.user_id == user_id)
    )
    place = db.execute(stmt).scalar_one_or_none()
    
    if not place:
        return None
        
    update_data = obj_in.model_dump(exclude_unset=True)
    
    if "pin_order" in update_data:
        old_order = place.pin_order
        new_order = update_data["pin_order"]
        
        if new_order is not None:
            new_order = max(1, min(3, new_order))
            
        place.pin_order = new_order
        
        target_tie = 0.5
        if old_order is not None and new_order is not None:
            if old_order < new_order:
                target_tie = 1.0
            elif old_order > new_order:
                target_tie = 0.0
        elif old_order is None and new_order is not None:
            target_tie = 0.0 
            
        all_places_stmt = select(SavedPlace).where(SavedPlace.user_id == user_id)
        all_places = list(db.execute(all_places_stmt).scalars().all())
        
        def sort_key(p):
            if p.pin_order is None:
                return (1, 999, 0.5)
            tie = target_tie if p.id == place.id else 0.5
            return (0, p.pin_order, tie)
            
        all_places.sort(key=sort_key)
        
        current_rank = 1
        for p in all_places:
            # We only reassign ranks to items that the user considers pinned (or the newly pinned one)
            if p.pin_order is not None and current_rank <= 3:
                p.pin_order = current_rank
                current_rank += 1
            else:
                p.pin_order = None
                
    for field, value in update_data.items():
        if field != "pin_order":
            setattr(place, field, value)
        
    if "latitude" in update_data and "longitude" in update_data:
        wkt_point = f"SRID=4326;POINT({update_data['longitude']} {update_data['latitude']})"
        place.geometry = wkt_point
        
    db.commit()
    db.refresh(place)
    return place
