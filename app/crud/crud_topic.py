from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.topic import Topic


class CRUDTopic:
    async def get_by_id(self, session: AsyncSession, topic_id: int) -> Optional[Topic]:
        return await session.get(Topic, topic_id)

    async def get_all(
        self,
        session: AsyncSession,
        grade: Optional[int] = None,
        block: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> List[Topic]:
        query = select(Topic).order_by(Topic.sort_order.asc(), Topic.id.asc())
        if grade is not None:
            query = query.where(Topic.grade == grade)
        if block:
            query = query.where(Topic.block == block)
        if is_active is not None:
            query = query.where(Topic.is_active == is_active)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        session: AsyncSession,
        block: str,
        title: str,
        grade: int = 9,
        sort_order: int = 0,
        is_active: bool = True,
    ) -> Topic:
        topic = Topic(
            grade=grade,
            block=block,
            title=title,
            sort_order=sort_order,
            is_active=is_active,
        )
        session.add(topic)
        await session.flush()
        return topic


crud_topic = CRUDTopic()
