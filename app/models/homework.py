from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class HomeworkStatus(str, Enum):
    ISSUED = "ISSUED"          # Выдано тьютором
    SUBMITTED = "SUBMITTED"    # Сдано учеником
    ACCEPTED = "ACCEPTED"      # Принято (верно)
    REVISION = "REVISION"      # Отправлено на доработку


class Homework(Base):
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    task_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    tutor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    task_photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    solution_photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default=HomeworkStatus.ISSUED.value, nullable=False)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Отношения
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="homework",
    )
    tutor: Mapped["User"] = relationship(
        "User",
        foreign_keys=[tutor_id],
        back_populates="issued_homeworks",
    )
    student: Mapped["User"] = relationship(
        "User",
        foreign_keys=[student_id],
        back_populates="received_homeworks",
    )

    def __repr__(self) -> str:
        return f"<Homework id={self.id} task_id={self.task_id} status={self.status}>"
