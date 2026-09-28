from typing import Optional
from pydantic import BaseModel, ConfigDict


class TopicBase(BaseModel):
    grade: int = 9
    block: str
    title: str
    sort_order: int = 0
    is_active: bool = True


class TopicCreate(TopicBase):
    pass


class TopicResponse(TopicBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TopicFilter(BaseModel):
    grade: Optional[int] = None
    block: Optional[str] = None
    is_active: Optional[bool] = True
