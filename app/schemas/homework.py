from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class HomeworkBase(BaseModel):
    task_text: str
    task_photo_url: Optional[str] = None


class HomeworkCreate(HomeworkBase):
    pass


class HomeworkSubmit(BaseModel):
    solution_photo_url: str


class HomeworkReview(BaseModel):
    is_accepted: bool
    feedback: Optional[str] = None


class HomeworkResponse(HomeworkBase):
    id: int
    task_id: int
    tutor_id: int
    student_id: int
    solution_photo_url: Optional[str] = None
    status: str
    feedback: Optional[str] = None
    bank_task_id: Optional[int] = None
    issued_at: datetime
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
