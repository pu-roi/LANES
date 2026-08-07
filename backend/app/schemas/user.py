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
from app.schemas.profile import ProfileResponse

class UserResponse(UserBase):
    id: int
    role_id: int
    is_active: bool
    created_at: datetime
    role: RoleResponse
    profile: Optional[ProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)


class UsersPaginatedResponse(BaseModel):
    users: list[UserResponse]
    total: int


class UserStatusUpdateRequest(BaseModel):
    is_active: bool
