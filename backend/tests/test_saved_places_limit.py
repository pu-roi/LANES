import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app import models, schemas, crud
from app.crud.saved_place import MAX_SAVED_PLACES

def test_saved_places_maximum_limit():
    """
    Test that users can save up to 10 places and an 11th place throws HTTPException (400).
    """
    db: Session = SessionLocal()
    try:
        # Create a unique test user
        username = "test_user_saved_places_limit"
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            user = models.User(
                username=username,
                email=f"{username}@lanes.ph",
                hashed_password="testpassword",
                role_id=1,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Clear any existing saved places for this user
        existing_places = crud.get_saved_places_by_user(db=db, user_id=user.id)
        for p in existing_places:
            crud.delete_saved_place(db=db, place_id=p.id, user_id=user.id)

        # Add 10 saved places
        for i in range(MAX_SAVED_PLACES):
            place_data = schemas.SavedPlaceCreate(
                name=f"Place {i + 1}",
                icon="🏠",
                address=f"Test Address {i + 1}",
                latitude=14.580 + (i * 0.001),
                longitude=121.070 + (i * 0.001)
            )
            created = crud.create_saved_place(db=db, obj_in=place_data, user_id=user.id)
            assert created.id is not None
            assert created.name == f"Place {i + 1}"

        current_places = crud.get_saved_places_by_user(db=db, user_id=user.id)
        assert len(current_places) == MAX_SAVED_PLACES

        # Attempt to add the 11th place - should fail with 400
        with pytest.raises(HTTPException) as exc_info:
            overflow_place = schemas.SavedPlaceCreate(
                name="Place 11 (Overflow)",
                icon="⭐",
                address="Overflow Address",
                latitude=14.590,
                longitude=121.080
            )
            crud.create_saved_place(db=db, obj_in=overflow_place, user_id=user.id)
        
        assert exc_info.value.status_code == 400
        assert "maximum limit of 10" in exc_info.value.detail

        # Delete 1 place
        first_place_id = current_places[0].id
        deleted = crud.delete_saved_place(db=db, place_id=first_place_id, user_id=user.id)
        assert deleted is True

        # Now creating the 10th place should succeed again
        re_add_place = schemas.SavedPlaceCreate(
            name="Place 10 (Replacement)",
            icon="⭐",
            address="Replacement Address",
            latitude=14.590,
            longitude=121.080
        )
        new_created = crud.create_saved_place(db=db, obj_in=re_add_place, user_id=user.id)
        assert new_created.id is not None

        # Clean up
        final_places = crud.get_saved_places_by_user(db=db, user_id=user.id)
        for p in final_places:
            crud.delete_saved_place(db=db, place_id=p.id, user_id=user.id)
        db.delete(user)
        db.commit()

    finally:
        db.close()
