from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
from typing import Optional


class ProfileBase(BaseModel):
    first_name: str
    last_name: str
    middle_initial: Optional[str] = None
    suffix: Optional[str] = None
    contact_number: Optional[str] = None
    birthdate: Optional[date] = None
    avatar_url: Optional[str] = None
    cover_color: Optional[str] = "#3B82F6"
    is_public: Optional[bool] = True
    trust_score: Optional[int] = 50
    reports_submitted: Optional[int] = 0
    reports_approved: Optional[int] = 0
    reports_rejected: Optional[int] = 0
    accuracy_rate: Optional[float] = 0.0


class ProfileCreate(ProfileBase):
    pass


from app.schemas.address import AddressUpdate, AddressResponse

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_initial: Optional[str] = None
    suffix: Optional[str] = None
    contact_number: Optional[str] = None
    birthdate: Optional[date] = None
    avatar_url: Optional[str] = None
    cover_color: Optional[str] = None
    is_public: Optional[bool] = None
    address: Optional[AddressUpdate] = None


from app.schemas.address import AddressResponse

class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    updated_at: datetime
    address: Optional[AddressResponse] = None

    model_config = ConfigDict(from_attributes=True)
