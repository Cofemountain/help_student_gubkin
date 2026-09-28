from enum import Enum
from typing import Optional
from sqlalchemy import BigInteger, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin


class BankType(str, Enum):
    OPEN = "OPEN"      # Открытый банк (для тренировки учеников)
    CLOSED = "CLOSED"  # Закрытый банк (для ДЗ преподавателей, без ответов в сети)


class BankTask(Base, TimestampMixin):
    __tablename__ = "bank_tasks"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    grade: Mapped[int] = mapped_column(SmallInteger, index=True, nullable=False)  # 7, 8, 9
    block: Mapped[str] = mapped_column(String(32), index=True, nullable=False)    # MECHANICS, THERMODYNAMICS, etc.
    bank_type: Mapped[str] = mapped_column(String(16), index=True, default=BankType.OPEN.value, nullable=False)  # OPEN / CLOSED
    topic_title: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), default="Базовый", nullable=False)  # Базовый, Средний, Повышенный
    answer: Mapped[str] = mapped_column(String(128), nullable=False)
    solution: Mapped[str] = mapped_column(Text, nullable=False)
    hint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<BankTask id={self.id} grade={self.grade} block={self.block} type={self.bank_type} title='{self.title[:20]}'>"
