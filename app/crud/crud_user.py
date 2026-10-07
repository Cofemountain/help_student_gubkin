from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole, OGELevel
from app.schemas.user import UserCreate


class CRUDUser:
    async def get_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
        return await session.get(User, user_id)

    async def get_by_telegram_id(self, session: AsyncSession, telegram_id: int) -> Optional[User]:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        session: AsyncSession,
        user_in: UserCreate,
        base_role: str = UserRole.STUDENT.value,
    ) -> tuple[User, bool]:
        """
        Возвращает (пользователь, был_ли_создан).
        Если пользователь уже есть — обновляет username/first_name/last_name.
        """
        user = await self.get_by_telegram_id(session, user_in.telegram_id)
        if user:
            # Обновляем имя, никнейм или аватар при изменениях
            if user_in.username is not None:
                user.username = user_in.username
            if user_in.first_name:
                user.first_name = user_in.first_name
            if user_in.last_name is not None:
                user.last_name = user_in.last_name
            if user_in.avatar_url:
                user.avatar_url = user_in.avatar_url
            await session.commit()
            await session.refresh(user)
            return user, False

        user = User(
            telegram_id=user_in.telegram_id,
            username=user_in.username,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            avatar_url=user_in.avatar_url,
            base_role=base_role,
            active_role=base_role,
            xp=0,
            level=OGELevel.GRADE_3.value,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user, True

    async def update_active_role(self, session: AsyncSession, user: User, new_role: str) -> User:
        """Переключение режима в WebApp ('student' <-> 'tutor')."""
        user.active_role = new_role
        await session.flush()
        return user

    async def get_all_tutor_tg_ids(self, session: AsyncSession) -> list[int]:
        """Возвращает Telegram ID всех пользователей с ролью tutor (для броадкаста)."""
        result = await session.execute(
            select(User.telegram_id).where(
                User.active_role == UserRole.TUTOR.value
            )
        )
        return [row[0] for row in result.fetchall() if row[0] is not None]


crud_user = CRUDUser()
