from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.core.database import Base

class SavedPlace(Base):
    """
    SavedPlace model for user's customized locations.
    """
    __tablename__ = "saved_places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(50))
    icon: Mapped[str] = mapped_column(String(50))
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Store explicit lat/lng for easy non-spatial frontend delivery
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    
    # Spatial column for future proximity queries
    geometry = mapped_column(Geometry("POINT", srid=4326, spatial_index=True))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="saved_places")
