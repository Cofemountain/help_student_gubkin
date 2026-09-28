from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserRoleUpdate(BaseModel):
    active_role: str  # "student" или "tutor"


class UserResponse(UserBase):
    id: int
    active_role: str
    base_role: str
    xp: int
    level: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
