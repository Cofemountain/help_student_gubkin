from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.task import Task, TaskPart, TaskStatus
from app.models.topic import Topic
from app.models.xp_transaction import XPReason
from app.schemas.task import TaskCreate
from app.services.gamification import award_xp


class CRUDTask:
    async def get_by_id(self, session: AsyncSession, task_id: int) -> Optional[Task]:
        query = (
            select(Task)
            .options(
                selectinload(Task.topic),
                selectinload(Task.student),
                selectinload(Task.tutor),
                selectinload(Task.homework),
            )
            .where(Task.id == task_id)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        student_id: int,
        task_in: TaskCreate,
    ) -> Task:
        task = Task(
            student_id=student_id,
            topic_id=task_in.topic_id,
            grade=task_in.grade or 9,
            part=task_in.part,
            photo_url=task_in.photo_url or "",
            question=task_in.question,
            scheduled_time=task_in.scheduled_time or "Сегодня",
            status=TaskStatus.OPEN.value,
            request_type=task_in.request_type or "TASK",
        )
        session.add(task)
        await session.flush()

        # Проверка: если это первая задача ученика, начисляем +50 XP
        tasks_count_result = await session.execute(
            select(func.count(Task.id)).where(Task.student_id == student_id)
        )
        count = tasks_count_result.scalar_one()
        if count == 1:
            # Начисляем +50 XP за дебют
            await award_xp(
                session=session,
                user_id=student_id,
                amount=50,
                reason=XPReason.FIRST_TASK.value,
                task_id=task.id,
            )

        # Загрузим связанные сущности
        return await self.get_by_id(session, task.id)  # type: ignore

    async def get_board_tasks(
        self,
        session: AsyncSession,
        status: Optional[str] = TaskStatus.OPEN.value,
        grade: Optional[int] = None,
        block: Optional[str] = None,
        part: Optional[str] = None,
    ) -> List[Task]:
        """Получение задач для доски (по умолчанию только OPEN)."""
        query = (
            select(Task)
            .outerjoin(Topic, Task.topic_id == Topic.id)
            .options(
                selectinload(Task.topic),
                selectinload(Task.student),
                selectinload(Task.tutor),
                selectinload(Task.homework),
            )
            .order_by(Task.id.desc(), Task.created_at.desc())
        )

        if status:
            query = query.where(Task.status == status)
        if grade is not None:
            query = query.where(Task.grade == grade)
        if block:
            query = query.where(Topic.block == block)
        if part:
            query = query.where(Task.part == part)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_student_tasks(
        self,
        session: AsyncSession,
        student_id: int,
        status: Optional[str] = None,
    ) -> List[Task]:
        query = (
            select(Task)
            .options(
                selectinload(Task.topic),
                selectinload(Task.student),
                selectinload(Task.tutor),
                selectinload(Task.homework),
            )
            .where(Task.student_id == student_id)
            .order_by(Task.id.desc(), Task.created_at.desc())
        )
        if status:
            query = query.where(Task.status == status)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_tutor_tasks(
        self,
        session: AsyncSession,
        tutor_id: int,
        status: Optional[str] = None,
    ) -> List[Task]:
        query = (
            select(Task)
            .options(
                selectinload(Task.topic),
                selectinload(Task.student),
                selectinload(Task.tutor),
                selectinload(Task.homework),
            )
            .where(Task.tutor_id == tutor_id)
            .order_by(Task.id.desc(), Task.created_at.desc())
        )
        if status:
            query = query.where(Task.status == status)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def accept_task(
        self,
        session: AsyncSession,
        task: Task,
        tutor_id: int,
    ) -> Task:
        """Тьютор берет задачу в работу (OPEN -> IN_PROGRESS)."""
        if task.status != TaskStatus.OPEN.value:
            raise ValueError(f"Нельзя взять в работу задачу в статусе {task.status}")

        task.tutor_id = tutor_id
        task.status = TaskStatus.IN_PROGRESS.value
        await session.flush()
        return task

    async def complete_task(
        self,
        session: AsyncSession,
        task: Task,
    ) -> tuple[Task, int, str]:
        """
        Ученик нажимает 'Вопрос решен' (IN_PROGRESS -> COMPLETED).
        Начисляются очки преподавателю (+100 XP) и ученику (+50 XP).
        Возвращает (обновленная_задача, новый_баланс_преподавателя, звание_преподавателя).
        """
        if task.status not in (TaskStatus.IN_PROGRESS.value, TaskStatus.HW_SUBMITTED.value):
            raise ValueError(f"Нельзя завершить задачу в статусе {task.status}")

        task.status = TaskStatus.COMPLETED.value
        await session.flush()

        tutor_xp = 0
        tutor_level = ""
        if task.tutor_id:
            _, tutor_xp, tutor_level = await award_xp(
                session=session,
                user_id=task.tutor_id,
                amount=100,
                reason=XPReason.TUTOR_SESSION.value,
                task_id=task.id,
            )

        if task.student_id:
            await award_xp(
                session=session,
                user_id=task.student_id,
                amount=50,
                reason="SESSION_COMPLETED",
                task_id=task.id,
            )

        return task, tutor_xp, tutor_level

    async def submit_review(
        self,
        session: AsyncSession,
        task: Task,
        teacher_response: Optional[str] = None,
        solution_photo_url: Optional[str] = None,
        telemost_url: Optional[str] = None,
        mark_completed: bool = True,
    ) -> Task:
        """Сохранение ответа преподавателя / ссылки на Телемост и завершение разбора."""
        if teacher_response is not None:
            task.teacher_response = teacher_response
        if solution_photo_url is not None:
            task.solution_photo_url = solution_photo_url
        if telemost_url is not None:
            task.telemost_url = telemost_url

        if mark_completed:
            task.status = TaskStatus.COMPLETED.value
            if task.tutor_id:
                await award_xp(
                    session=session,
                    user_id=task.tutor_id,
                    amount=100,
                    reason=XPReason.TUTOR_SESSION.value,
                    task_id=task.id,
                )
            if task.student_id:
                await award_xp(
                    session=session,
                    user_id=task.student_id,
                    amount=50,
                    reason="SESSION_COMPLETED",
                    task_id=task.id,
                )
        await session.flush()
        return await self.get_by_id(session, task.id)

    async def get_solved_tasks(
        self,
        session: AsyncSession,
        grade: Optional[int] = None,
        block: Optional[str] = None,
        topic_id: Optional[int] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Task]:
        """
        Получение базы разобранных задач (решённых заявок) для Банка заданий.
        Заявка включается, если она имеет статус COMPLETED или заполнен teacher_response.
        """
        query = (
            select(Task)
            .join(Topic, Task.topic_id == Topic.id)
            .options(
                selectinload(Task.topic),
                selectinload(Task.student),
                selectinload(Task.tutor),
                selectinload(Task.homework),
            )
            .where(
                (
                    (Task.teacher_response.isnot(None))
                    & (func.length(func.trim(Task.teacher_response)) > 10)
                )
                | (
                    (Task.solution_photo_url.isnot(None))
                    & (Task.solution_photo_url != "")
                )
            )
            .where(
                Task.status.in_([TaskStatus.COMPLETED.value, TaskStatus.IN_PROGRESS.value])
            )
            .order_by(Task.updated_at.desc(), Task.created_at.desc())
        )

        if grade is not None:
            query = query.where(Task.grade == grade)
        if block:
            query = query.where(Topic.block == block)
        if topic_id:
            query = query.where(Task.topic_id == topic_id)
        if search:
            search_str = f"%{search.strip()}%"
            query = query.where(
                Task.question.ilike(search_str)
                | Task.teacher_response.ilike(search_str)
                | Topic.title.ilike(search_str)
            )

        query = query.limit(limit).offset(offset)
        result = await session.execute(query)
        return list(result.scalars().all())


crud_task = CRUDTask()
