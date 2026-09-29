from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.topic import TopicResponse
from app.schemas.user import UserResponse
from app.schemas.homework import HomeworkResponse


class TaskBase(BaseModel):
    topic_id: int
    grade: Optional[int] = 9
    part: str = "PART_1"  # PART_1 (тестовая) / PART_2 (развернутая)
    photo_url: Optional[str] = ""
    question: str
    scheduled_time: Optional[str] = "Сегодня"
    request_type: Optional[str] = "TASK"  # "TASK" или "TELEMOST"
    telemost_url: Optional[str] = ""
    teacher_response: Optional[str] = ""
    solution_photo_url: Optional[str] = ""
    student_clarification: Optional[str] = ""


class TaskCreate(TaskBase):
    pass


class TaskAccept(BaseModel):
    tutor_id: int


class TaskReviewCreate(BaseModel):
    teacher_response: Optional[str] = ""
    solution_photo_url: Optional[str] = ""
    telemost_url: Optional[str] = ""
    status: Optional[str] = "IN_PROGRESS"  # По умолчанию ответ сохраняется, а ученик закрывает заявку


class TaskClarifyRequest(BaseModel):
    clarification: str


class TelemostUrlUpdate(BaseModel):
    telemost_url: str


class TaskResponse(TaskBase):
    id: int
    student_id: int
    tutor_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime

    topic: Optional[TopicResponse] = None
    student: Optional[UserResponse] = None
    tutor: Optional[UserResponse] = None
    homework: Optional[HomeworkResponse] = None

    model_config = ConfigDict(from_attributes=True)


class TaskFilter(BaseModel):
    grade: Optional[int] = None
    status: Optional[str] = None
    part: Optional[str] = None
    topic_id: Optional[int] = None
    block: Optional[str] = None
