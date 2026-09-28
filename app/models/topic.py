from enum import Enum
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.task import Task


class OGEBlock(str, Enum):
    MECHANICS = "MECHANICS"                    # Механические явления
    THERMODYNAMICS = "THERMODYNAMICS"          # Тепловые явления
    ELECTRODYNAMICS = "ELECTRODYNAMICS"        # Электромагнитные явления
    QUANTUM = "QUANTUM"                        # Квантовые явления
    PART_2_ADVANCED = "PART_2_ADVANCED"        # Вторая часть (№20–25 ОГЭ)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grade: Mapped[int] = mapped_column(Integer, default=9, nullable=False, index=True)
    block: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="topic",
    )

    def __repr__(self) -> str:
        return f"<Topic id={self.id} block={self.block} title='{self.title[:30]}...'>"
