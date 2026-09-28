from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, OGELevel
from app.models.xp_transaction import XPTransaction, XPReason


def calculate_oge_level(total_xp: int) -> str:
    """
    Расчет ранга ОГЭ на основе накопленного опыта:
    - 0–200 XP:   Порог сдачи (Оценка 3)
    - 201–600 XP: Уверенная 4-ка (Оценка 4)
    - 600+ XP:    Отличник ОГЭ (Оценка 5)
    """
    if total_xp >= 600:
        return OGELevel.GRADE_5.value
    elif total_xp >= 201:
        return OGELevel.GRADE_4.value
    return OGELevel.GRADE_3.value


def get_user_title(role: str, xp: int) -> dict:
    """
    Возвращает подробную информацию о звании для преподавателя или ученика.
    """
    if role == "tutor":
        if xp >= 1000:
            return {
                "badge": "🏆",
                "title": "Заслуженный преподаватель",
                "full_title": "🏆 Заслуженный преподаватель",
                "next_title": None,
                "needed_xp": 0,
                "xp_to_next": 0,
            }
        elif xp >= 500:
            return {
                "badge": "🥇",
                "title": "Мастер физики",
                "full_title": "🥇 Мастер физики",
                "next_title": "Заслуженный преподаватель",
                "needed_xp": 1000,
                "xp_to_next": 1000 - xp,
            }
        elif xp >= 150:
            return {
                "badge": "🥈",
                "title": "Опытный наставник",
                "full_title": "🥈 Опытный наставник",
                "next_title": "Мастер физики",
                "needed_xp": 500,
                "xp_to_next": 500 - xp,
            }
        else:
            return {
                "badge": "🥉",
                "title": "Наставник-стажёр",
                "full_title": "🥉 Наставник-стажёр",
                "next_title": "Опытный наставник",
                "needed_xp": 150,
                "xp_to_next": 150 - xp,
            }
    else:
        if xp >= 500:
            return {
                "badge": "🥇",
                "title": "Мастер физики",
                "full_title": "🥇 Мастер физики",
                "next_title": None,
                "needed_xp": 0,
                "xp_to_next": 0,
            }
        elif xp >= 150:
            return {
                "badge": "🥈",
                "title": "Знаток законов физики",
                "full_title": "🥈 Знаток законов физики",
                "next_title": "Мастер физики",
                "needed_xp": 500,
                "xp_to_next": 500 - xp,
            }
        else:
            return {
                "badge": "🥉",
                "title": "Юный наблюдатель",
                "full_title": "🥉 Юный наблюдатель",
                "next_title": "Знаток законов физики",
                "needed_xp": 150,
                "xp_to_next": 150 - xp,
            }


async def award_xp(
    session: AsyncSession,
    user_id: int,
    amount: int,
    reason: str,
    task_id: int | None = None,
) -> tuple[bool, int, str]:
    """
    Начисление XP с гарантией идемпотентности (защита от повторного начисления).
    Возвращает (успех_начисления, новый_баланс_xp, новый_уровень).
    """
    # 1. Проверяем, не было ли уже начисления по этой задаче и причине
    query = select(XPTransaction).where(
        XPTransaction.user_id == user_id,
        XPTransaction.reason == reason,
    )
    if task_id is not None:
        query = query.where(XPTransaction.task_id == task_id)

    result = await session.execute(query)
    existing_tx = result.scalar_one_or_none()
    if existing_tx:
        # Уже начислено ранее
        user = await session.get(User, user_id)
        return False, (user.xp if user else 0), (user.level if user else OGELevel.GRADE_3.value)

    # 2. Получаем пользователя
    user = await session.get(User, user_id)
    if not user:
        raise ValueError(f"Пользователь с id={user_id} не найден")

    # 3. Фиксируем транзакцию
    tx = XPTransaction(
        user_id=user_id,
        task_id=task_id,
        amount=amount,
        reason=reason,
    )
    session.add(tx)

    # 4. Обновляем баланс пользователя и пересчитываем ранг
    user.xp += amount
    user.level = calculate_oge_level(user.xp)

    await session.flush()
    return True, user.xp, user.level
