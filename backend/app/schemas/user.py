from datetime import datetime
from pydantic import BaseModel, ConfigDict


from app.schemas.role import RoleResponse

class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str
    role_id: int = 4  # Default to Commuter (id=4)
    is_active: bool = True


from typing import Optional
from pydantic import field_serializer
from app.schemas.common import serialize_utc_datetime
from app.schemas.profile import ProfileResponse

class UserResponse(UserBase):
    id: int
    role_id: int
    is_active: bool
    created_at: datetime
    role: RoleResponse
    profile: Optional[ProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_user_datetimes(self, dt: datetime, _info):
        return serialize_utc_datetime(dt)


class UsersPaginatedResponse(BaseModel):
    users: list[UserResponse]
    total: int


class UserStatusUpdateRequest(BaseModel):
    is_active: bool

class UserRoleUpdateRequest(BaseModel):
    role_id: int


class PasswordChangeOtpRequest(BaseModel):
    current_password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    otp_code: str

