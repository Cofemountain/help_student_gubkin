from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.base import utc_now
from app.models.homework import Homework, HomeworkStatus
from app.models.task import Task, TaskStatus
from app.models.xp_transaction import XPReason
from app.schemas.homework import HomeworkCreate
from app.services.gamification import award_xp


class CRUDHomework:
    async def get_by_id(self, session: AsyncSession, homework_id: int) -> Optional[Homework]:
        query = (
            select(Homework)
            .options(
                selectinload(Homework.task),
                selectinload(Homework.tutor),
                selectinload(Homework.student),
            )
            .where(Homework.id == homework_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_task_id(self, session: AsyncSession, task_id: int) -> Optional[Homework]:
        query = select(Homework).where(Homework.task_id == task_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        task: Task,
        tutor_id: int,
        homework_in: HomeworkCreate,
    ) -> Homework:
        """Тьютор выдает ДЗ формата ОГЭ после проведенного разбора."""
        if task.status != TaskStatus.IN_PROGRESS.value:
            raise ValueError(f"Выдать ДЗ можно только для задачи в статусе IN_PROGRESS (текущий: {task.status})")
        if task.tutor_id != tutor_id:
            raise ValueError("Выдать ДЗ может только назначенный на задачу тьютор")

        existing_hw = await self.get_by_task_id(session, task.id)
        if existing_hw:
            # Обновление существующего задания
            existing_hw.task_text = homework_in.task_text
            existing_hw.task_photo_url = homework_in.task_photo_url
            existing_hw.status = HomeworkStatus.ISSUED.value
            existing_hw.issued_at = utc_now()
            await session.flush()
            return existing_hw

        homework = Homework(
            task_id=task.id,
            tutor_id=tutor_id,
            student_id=task.student_id,
            task_text=homework_in.task_text,
            task_photo_url=homework_in.task_photo_url,
            status=HomeworkStatus.ISSUED.value,
        )
        session.add(homework)
        await session.flush()
        return homework

    async def submit_solution(
        self,
        session: AsyncSession,
        homework: Homework,
        solution_photo_url: str,
        student_id: int,
    ) -> Homework:
        """Ученик загружает фото решения ДЗ по критериям ОГЭ."""
        if homework.student_id != student_id:
            raise ValueError("Сдать решение может только автор задачи")

        homework.solution_photo_url = solution_photo_url
        homework.status = HomeworkStatus.SUBMITTED.value
        homework.submitted_at = utc_now()

        # Обновляем статус связанной задачи на HW_SUBMITTED
        task = await session.get(Task, homework.task_id)
        if task:
            task.status = TaskStatus.HW_SUBMITTED.value

        await session.flush()
        return homework

    async def review_solution(
        self,
        session: AsyncSession,
        homework: Homework,
        is_accepted: bool,
        feedback: Optional[str],
        tutor_id: int,
    ) -> tuple[Homework, Task]:
        """Тьютор проверяет решение: принимает или отправляет на доработку."""
        if homework.tutor_id != tutor_id:
            raise ValueError("Проверить решение может только назначенный тьютор")

        task = await session.get(Task, homework.task_id)
        if not task:
            raise ValueError("Связанная задача не найдена")

        homework.feedback = feedback
        homework.reviewed_at = utc_now()

        if is_accepted:
            # Решение принято верно
            homework.status = HomeworkStatus.ACCEPTED.value
            task.status = TaskStatus.COMPLETED.value

            # Начисление XP согласно ТЗ ОГЭ:
            # 1. Ученику: +100 XP за принятое ДЗ
            await award_xp(
                session=session,
                user_id=homework.student_id,
                amount=100,
                reason=XPReason.HW_SOLVED.value,
                task_id=task.id,
            )
            # 2. Тьютору: +100 XP за проведенную сессию разбора
            await award_xp(
                session=session,
                user_id=homework.tutor_id,
                amount=100,
                reason=XPReason.TUTOR_SESSION.value,
                task_id=task.id,
            )
            # 3. Тьютору: +50 XP за проверку ДЗ по критериям
            await award_xp(
                session=session,
                user_id=homework.tutor_id,
                amount=50,
                reason=XPReason.HW_CHECKED.value,
                task_id=task.id,
            )
        else:
            # Отправлено на доработку (ошибки в оформлении или расчете)
            homework.status = HomeworkStatus.REVISION.value
            task.status = TaskStatus.IN_PROGRESS.value

        await session.flush()
        return homework, task


crud_homework = CRUDHomework()
