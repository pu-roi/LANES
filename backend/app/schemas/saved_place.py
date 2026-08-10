from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class SavedPlaceBase(BaseModel):
    name: str = Field(..., max_length=50, description="Name of the saved place (e.g. Home, Work)")
    icon: str = Field(..., max_length=50, description="Lucide icon name (e.g. Home, Briefcase)")
    address: Optional[str] = Field(None, max_length=255, description="Human readable address")
    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location")

class SavedPlaceCreate(SavedPlaceBase):
    pass

class SavedPlaceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    icon: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class SavedPlaceResponse(SavedPlaceBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
