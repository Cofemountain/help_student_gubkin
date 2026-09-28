from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import utc_now

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class XPReason(str, Enum):
    FIRST_TASK = "FIRST_TASK"          # +50 XP за первую созданную задачу ОГЭ
    TUTOR_SESSION = "TUTOR_SESSION"    # +100 XP тьютору за разбор
    HW_SOLVED = "HW_SOLVED"            # +100 XP ученику за принятое ДЗ
    HW_CHECKED = "HW_CHECKED"          # +50 XP тьютору за проверку ДЗ
    BANK_SOLVED = "BANK_SOLVED"        # +15 XP за верное решение задачи из банка


class XPTransaction(Base):
    __tablename__ = "xp_transactions"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    task_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Отношения
    user: Mapped["User"] = relationship(
        "User",
        back_populates="xp_transactions",
    )
    task: Mapped[Optional["Task"]] = relationship(
        "Task",
        back_populates="xp_transactions",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "task_id", "reason", name="uq_user_task_reason"),
    )

    def __repr__(self) -> str:
        return f"<XPTransaction id={self.id} user_id={self.user_id} +{self.amount} reason={self.reason}>"
