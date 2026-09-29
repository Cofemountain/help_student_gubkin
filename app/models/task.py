from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.topic import Topic
    from app.models.homework import Homework
    from app.models.xp_transaction import XPTransaction


class TaskPart(str, Enum):
    PART_1 = "PART_1"  # Тестовая / Базовая часть ОГЭ
    PART_2 = "PART_2"  # Вторая часть ОГЭ (развернутый ответ)


class TaskStatus(str, Enum):
    OPEN = "OPEN"                      # Открыта, ожидает тьютора
    IN_PROGRESS = "IN_PROGRESS"        # Взята в работу тьютором
    UNDERSTOOD = "UNDERSTOOD"          # Ученик подтвердил понимание, ожидает задачу из закрытого банка
    HW_ISSUED = "HW_ISSUED"            # Задача из закрытого банка выдана ученику
    HW_SUBMITTED = "HW_SUBMITTED"      # ДЗ сдано учеником на проверку
    COMPLETED = "COMPLETED"            # Разбор завершен, ДЗ принято
    CANCELLED = "CANCELLED"            # Отменена


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    tutor_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    topic_id: Mapped[int] = mapped_column(Integer, ForeignKey("topics.id", ondelete="RESTRICT"), index=True, nullable=False)
    grade: Mapped[int] = mapped_column(Integer, default=9, nullable=False, index=True)

    part: Mapped[str] = mapped_column(String(16), default=TaskPart.PART_1.value, nullable=False)
    photo_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    question: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_time: Mapped[str] = mapped_column(String(64), nullable=False, default="Сегодня")
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.OPEN.value, index=True, nullable=False)
    request_type: Mapped[str] = mapped_column(String(32), default="TASK", nullable=False)  # "TASK" или "TELEMOST"
    telemost_url: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, default="")
    teacher_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    solution_photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    student_clarification: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")

    # Отношения
    student: Mapped["User"] = relationship(
        "User",
        foreign_keys=[student_id],
        back_populates="created_tasks",
    )
    tutor: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[tutor_id],
        back_populates="accepted_tasks",
    )
    topic: Mapped["Topic"] = relationship(
        "Topic",
        back_populates="tasks",
    )
    homework: Mapped[Optional["Homework"]] = relationship(
        "Homework",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
    )
    xp_transactions: Mapped[List["XPTransaction"]] = relationship(
        "XPTransaction",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_tasks_status_part", "status", "part"),
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} status={self.status} part={self.part} topic_id={self.topic_id}>"
