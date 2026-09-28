from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BankTaskBase(BaseModel):
    grade: int
    block: str
    bank_type: str
    topic_title: str
    title: str
    statement: str
    difficulty: str
    hint: Optional[str] = None


class BankTaskStudentResponse(BankTaskBase):
    """Схема задачи для открытого банка (ученикам не отдаем эталонный ответ и решение сразу)."""
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BankTaskTutorResponse(BankTaskBase):
    """Схема задачи для закрытого банка преподавателя (включает эталонный ответ и критерии решения)."""
    id: int
    answer: str
    solution: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CheckAnswerRequest(BaseModel):
    user_answer: str
    student_tg_id: Optional[int] = None


class CheckAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: Optional[str] = None
    solution: Optional[str] = None
    xp_awarded: int = 0
    message: str


class AssignHomeworkRequest(BaseModel):
    task_id: int              # ID задачи взаимопомощи (IN_PROGRESS)
    bank_task_id: int         # ID задачи из закрытого банка
    tutor_tg_id: int          # Telegram ID преподавателя
