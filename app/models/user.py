from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.homework import Homework
    from app.models.xp_transaction import XPTransaction


class UserRole(str, Enum):
    STUDENT = "student"
    TUTOR = "tutor"
    ADMIN = "admin"


class OGELevel(str, Enum):
    GRADE_3 = "grade_3"  # Порог сдачи (Оценка 3)
    GRADE_4 = "grade_4"  # Уверенная 4-ка (Оценка 4)
    GRADE_5 = "grade_5"  # Отличник ОГЭ (Оценка 5)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Роли пользователя: активный режим в WebApp и базовая роль
    active_role: Mapped[str] = mapped_column(String(16), default=UserRole.STUDENT.value, nullable=False)
    base_role: Mapped[str] = mapped_column(String(16), default=UserRole.STUDENT.value, nullable=False)

    # Геймификация подготовки к ОГЭ
    xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[str] = mapped_column(String(32), default=OGELevel.GRADE_3.value, nullable=False)

    # Связи
    created_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        foreign_keys="Task.student_id",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    accepted_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        foreign_keys="Task.tutor_id",
        back_populates="tutor",
    )
    issued_homeworks: Mapped[List["Homework"]] = relationship(
        "Homework",
        foreign_keys="Homework.tutor_id",
        back_populates="tutor",
    )
    received_homeworks: Mapped[List["Homework"]] = relationship(
        "Homework",
        foreign_keys="Homework.student_id",
        back_populates="student",
    )
    xp_transactions: Mapped[List["XPTransaction"]] = relationship(
        "XPTransaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} tg={self.telegram_id} role={self.active_role} xp={self.xp} level={self.level}>"
