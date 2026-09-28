from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.bank_task import BankTask, BankType


class CRUDBankTask:
    async def get_by_id(self, session: AsyncSession, task_id: int) -> Optional[BankTask]:
        query = select(BankTask).where(BankTask.id == task_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_tasks(
        self,
        session: AsyncSession,
        grade: Optional[int] = None,
        block: Optional[str] = None,
        bank_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[BankTask]:
        query = select(BankTask)
        if grade is not None:
            query = query.where(BankTask.grade == grade)
        if block is not None:
            query = query.where(BankTask.block == block)
        if bank_type is not None:
            query = query.where(BankTask.bank_type == bank_type)
        query = query.order_by(BankTask.id.asc()).limit(limit).offset(offset)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_available_blocks(
        self,
        session: AsyncSession,
        grade: int,
        bank_type: str,
    ) -> List[str]:
        query = (
            select(BankTask.block)
            .where(BankTask.grade == grade, BankTask.bank_type == bank_type)
            .distinct()
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def count_tasks(
        self,
        session: AsyncSession,
        grade: Optional[int] = None,
        block: Optional[str] = None,
        bank_type: Optional[str] = None,
    ) -> int:
        query = select(func.count(BankTask.id))
        if grade is not None:
            query = query.where(BankTask.grade == grade)
        if block is not None:
            query = query.where(BankTask.block == block)
        if bank_type is not None:
            query = query.where(BankTask.bank_type == bank_type)
        result = await session.execute(query)
        return result.scalar_one() or 0


crud_bank_task = CRUDBankTask()
