import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.crud.crud_user import crud_user
from app.crud.crud_topic import crud_topic
from app.crud.crud_task import crud_task
from app.crud.crud_homework import crud_homework
from app.crud.crud_bank_task import crud_bank_task
from app.models.user import UserRole
from app.models.xp_transaction import XPReason
from app.schemas.user import UserCreate, UserRoleUpdate, UserResponse
from app.schemas.topic import TopicResponse
from app.schemas.task import TaskCreate, TaskResponse, TaskReviewCreate, TaskClarifyRequest
from app.schemas.homework import HomeworkCreate, HomeworkSubmit, HomeworkReview, HomeworkResponse
from app.schemas.bank_task import (
    BankTaskStudentResponse,
    BankTaskTutorResponse,
    CheckAnswerRequest,
    CheckAnswerResponse,
    AssignHomeworkRequest,
)
from app.services.gamification import award_xp
from app.services.notifications import (
    notify_task_accepted,
    notify_review_submitted,
    notify_task_completed,
    notify_new_task_to_tutors,
    notify_student_clarification,
    notify_student_understood,
    notify_homework_issued,
)

router = APIRouter(prefix="/api", tags=["OGE Physics"])


# ==========================================
# 1. ТЕМЫ И КОДИФИКАТОР ОГЭ
# ==========================================
@router.get("/topics", response_model=List[TopicResponse], summary="Получить темы по физике (7–9 классы / ОГЭ)")
async def get_topics(
    grade: Optional[int] = Query(None, description="Класс: 7, 8 или 9"),
    block: Optional[str] = Query(None, description="Раздел физики"),
    session: AsyncSession = Depends(get_db),
):
    return await crud_topic.get_all(session, grade=grade, block=block, is_active=True)


# ==========================================
# 2. ПОЛЬЗОВАТЕЛИ
# ==========================================
@router.post("/users/sync", response_model=UserResponse, summary="Регистрация / получение профиля по Telegram")
async def sync_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_db),
):
    user, _ = await crud_user.get_or_create(session, user_in)
    return user


@router.get("/users/by-telegram/{telegram_id}", response_model=UserResponse, summary="Получить профиль по Telegram/MAX ID")
async def get_user_by_telegram_id(
    telegram_id: int,
    session: AsyncSession = Depends(get_db),
):
    user = await crud_user.get_by_telegram_id(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.patch("/users/{telegram_id}/role", response_model=UserResponse, summary="Переключение роли в WebApp (student <-> tutor)")
async def update_role(
    telegram_id: int,
    role_in: UserRoleUpdate,
    session: AsyncSession = Depends(get_db),
):
    user = await crud_user.get_by_telegram_id(session, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    updated_user = await crud_user.update_active_role(session, user, role_in.active_role)

    # Автоматически обновляем меню и отправляем подтверждение в чат МАКС
    try:
        from bot_max import MaxBotClient, get_main_menu_buttons, get_user_title
        from app.core.config import settings
        if settings.MAX_BOT_TOKEN:
            client = MaxBotClient(settings.MAX_BOT_TOKEN)
            role_name = "👨‍🏫 Преподаватель (Наставник)" if role_in.active_role == "tutor" else "🎓 Обучающийся (Ученик)"
            title_info = get_user_title(updated_user.active_role, updated_user.xp)
            full_name = f"{updated_user.first_name} {updated_user.last_name or ''}".strip()
            text = (
                f"Здравствуйте, {full_name}!\n\n"
                f"Рабочий профиль успешно переключен: {role_name}\n\n"
                f"Ваш квалификационный статус:\n"
                f"• Квалификационная категория: {title_info['full_title']}\n"
                f"• Накопленный рейтинг: {updated_user.xp} XP\n\n"
                f"Клавиатура и доступные разделы меню обновлены!"
            )
            buttons = get_main_menu_buttons(updated_user.active_role, user=updated_user)
            await client.send_message(user_id=telegram_id, text=text, buttons=buttons)
            await client.close()
    except Exception as e:
        logger.warning(f"Не удалось отправить уведомление о смене роли в MAX: {e}")

    return updated_user


# ==========================================
# 3. ДОСКА И ЗАДАЧИ ОГЭ
# ==========================================
@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, summary="Создать заявку на разбор задачи")
async def create_task(
    task_in: TaskCreate,
    student_tg_id: int = Query(..., description="Telegram ID ученика"),
    session: AsyncSession = Depends(get_db),
):
    user = await crud_user.get_by_telegram_id(session, student_tg_id)
    if not user:
        user, _ = await crud_user.get_or_create(
            session,
            UserCreate(
                telegram_id=student_tg_id,
                first_name="Алексей",
                username="alex_student",
                active_role="student",
                is_student=True,
            ),
        )
    task = await crud_task.create(session, student_id=user.id, task_in=task_in)

    # Уведомить всех преподавателей о новой задаче (async background)
    try:
        topic_title = task.topic.title if task.topic else "Физика (ОГЭ)"
        tutor_ids = await crud_user.get_all_tutor_tg_ids(session)
        asyncio.ensure_future(
            notify_new_task_to_tutors(
                tutor_tg_ids=tutor_ids,
                task_id=task.id,
                topic_title=topic_title,
                student_name=user.first_name,
                question=task.question or "",
                scheduled_time=task.scheduled_time,
            )
        )
    except Exception:
        pass  # Не блокируем ответ из-за уведомления

    return task


@router.get("/tasks", response_model=List[TaskResponse], summary="Получить задачи для доски (фильтрация по классу/блоку/части)")
async def get_board_tasks(
    status_filter: Optional[str] = Query("OPEN", description="Статус задачи"),
    grade: Optional[int] = Query(None, description="Класс: 7, 8 или 9"),
    block: Optional[str] = Query(None, description="Раздел физики"),
    part: Optional[str] = Query(None, description="PART_1 или PART_2"),
    session: AsyncSession = Depends(get_db),
):
    return await crud_task.get_board_tasks(session, status=status_filter, grade=grade, block=block, part=part)


@router.get("/tasks/my", response_model=List[TaskResponse], summary="Получить мои задачи (ученика или тьютора)")
async def get_my_tasks(
    telegram_id: int = Query(...),
    as_role: str = Query("student", description="'student' или 'tutor'"),
    session: AsyncSession = Depends(get_db),
):
    user = await crud_user.get_by_telegram_id(session, telegram_id)
    if not user:
        is_tut = as_role == "tutor"
        user, _ = await crud_user.get_or_create(
            session,
            UserCreate(
                telegram_id=telegram_id,
                first_name="Преподаватель" if is_tut else "Обучающийся",
                username=None,
                active_role="tutor" if is_tut else "student",
            ),
        )

    if as_role == "tutor":
        return await crud_task.get_tutor_tasks(session, tutor_id=user.id)
    return await crud_task.get_student_tasks(session, student_id=user.id)


@router.get("/tasks/{task_id}", response_model=TaskResponse, summary="Получить детали задачи")
async def get_task_detail(
    task_id: int,
    session: AsyncSession = Depends(get_db),
):
    task = await crud_task.get_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@router.post("/tasks/{task_id}/accept", response_model=TaskResponse, summary="Тьютор берет задачу в работу")
async def accept_task(
    task_id: int,
    tutor_tg_id: int = Query(...),
    session: AsyncSession = Depends(get_db),
):
    task = await crud_task.get_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    tutor = await crud_user.get_by_telegram_id(session, tutor_tg_id)
    if not tutor:
        tutor, _ = await crud_user.get_or_create(
            session,
            UserCreate(
                telegram_id=tutor_tg_id,
                first_name="Михаил Сергеевич",
                username="physics_tutor",
                active_role="tutor",
                is_tutor=True,
            ),
        )

    if (task.student and task.student.telegram_id == tutor_tg_id) or (tutor and task.student_id == tutor.id):
        raise HTTPException(status_code=400, detail="Преподаватель не может взять на разбор собственную заявку")

    try:
        updated_task = await crud_task.accept_task(session, task, tutor_id=tutor.id)
        result = await crud_task.get_by_id(session, updated_task.id)

        # Push-уведомления ученику и преподавателю
        try:
            student = result.student
            topic_title = result.topic.title if result.topic else "Физика (ОГЭ)"
            asyncio.ensure_future(
                notify_task_accepted(
                    student_tg_id=student.telegram_id,
                    tutor_tg_id=tutor_tg_id,
                    task_id=task_id,
                    topic_title=topic_title,
                    student_name=student.first_name,
                    tutor_name=tutor.first_name,
                    scheduled_time=result.scheduled_time,
                    tutor_username=tutor.username,
                    student_username=student.username,
                )
            )
        except Exception:
            pass

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/review", response_model=TaskResponse, summary="Преподаватель отправляет текстовый разбор или ссылку на созвон")
async def review_task(
    task_id: int,
    review_in: TaskReviewCreate,
    tutor_tg_id: int = Query(...),
    session: AsyncSession = Depends(get_db),
):
    task = await crud_task.get_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    tutor = await crud_user.get_by_telegram_id(session, tutor_tg_id)
    if not tutor:
        tutor, _ = await crud_user.get_or_create(
            session,
            UserCreate(
                telegram_id=tutor_tg_id,
                first_name="Михаил Сергеевич",
                username="physics_tutor",
                active_role="tutor",
                is_tutor=True,
            ),
        )

    if not task.tutor_id:
        task.tutor_id = tutor.id

    mark_completed = review_in.status == "COMPLETED"
    updated_task = await crud_task.submit_review(
        session,
        task,
        teacher_response=review_in.teacher_response,
        solution_photo_url=review_in.solution_photo_url,
        telemost_url=review_in.telemost_url,
        mark_completed=mark_completed,
    )

    # Push-уведомление ученику о разборе
    try:
        student = updated_task.student
        topic_title = updated_task.topic.title if updated_task.topic else "Физика (ОГЭ)"
        asyncio.ensure_future(
            notify_review_submitted(
                student_tg_id=student.telegram_id,
                task_id=task_id,
                topic_title=topic_title,
                tutor_name=tutor.first_name,
                teacher_response=review_in.teacher_response,
                telemost_url=review_in.telemost_url,
                tutor_username=tutor.username,
            )
        )
    except Exception:
        pass

    return updated_task


@router.post("/tasks/{task_id}/telemost", response_model=TaskResponse, summary="Быстрое создание видеокомнаты Телемоста")
async def create_telemost_room(
    task_id: int,
    tutor_tg_id: int = Query(...),
    session: AsyncSession = Depends(get_db),
):
    import time
    task = await crud_task.get_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    room_code = 7000000000 + (task_id * 10007) % 2000000000
    room_url = f"https://telemost.yandex.ru/j/{room_code}"
    updated_task = await crud_task.submit_review(
        session,
        task,
        telemost_url=room_url,
        mark_completed=False,
    )
    return updated_task


@router.post("/tasks/{task_id}/clarify", response_model=TaskResponse, summary="Ученик задает уточняющий вопрос по заявке (если не понял разбор)")
async def clarify_task_endpoint(
    task_id: int,
    req: TaskClarifyRequest,
    student_tg_id: int = Query(..., description="Telegram ID ученика"),
    session: AsyncSession = Depends(get_db),
):
    task = await crud_task.get_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    task.student_clarification = req.clarification
    await session.flush()
    result = await crud_task.get_by_id(session, task.id)

    # Push-уведомление преподавателю о том, что ученик задал уточняющий вопрос
    try:
        if result.tutor:
            topic_title = result.topic.title if result.topic else "Физика"
            student_name = result.student.first_name if result.student else "Ученик"
            asyncio.ensure_future(
                notify_student_clarification(
                    tutor_tg_id=result.tutor.telegram_id,
                    task_id=task_id,
                    topic_title=topic_title,
                    student_name=student_name,
                    clarification=req.clarification,
                )
            )
    except Exception:
        pass

@router.post("/tasks/{task_id}/understood", response_model=TaskResponse, summary="Ученик подтверждает понимание темы и ожидает контрольную задачу")
async def mark_task_understood_endpoint(
    task_id: int,
    student_tg_id: int = Query(..., description="ID ученика"),
    session: AsyncSession = Depends(get_db),
):
    task = await crud_task.get_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    task.status = "UNDERSTOOD"
    await session.flush()
    result = await crud_task.get_by_id(session, task.id)

    # Push-уведомление преподавателю о том, что ученик понял тему и ждет задачу
    try:
        if result.tutor:
            topic_title = result.topic.title if result.topic else "Физика (ОГЭ)"
            student_name = result.student.first_name if result.student else "Ученик"
            asyncio.ensure_future(
                notify_student_understood(
                    tutor_tg_id=result.tutor.telegram_id,
                    task_id=task_id,
                    topic_title=topic_title,
                    student_name=student_name,
                )
            )
    except Exception:
        pass

    return result


@router.post("/tasks/{task_id}/check-homework", response_model=CheckAnswerResponse, summary="Проверить ответ ученика на контрольную задачу из закрытого банка")
async def check_task_homework_endpoint(
    task_id: int,
    check_in: CheckAnswerRequest,
    session: AsyncSession = Depends(get_db),
):
    task = await crud_task.get_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    hw = await crud_homework.get_by_task_id(session, task_id)
    if not hw:
        raise HTTPException(status_code=400, detail="К этой заявке еще не прикреплено задание")

    bank_task = None
    if hw.bank_task_id:
        bank_task = await crud_bank_task.get_by_id(session, hw.bank_task_id)

    correct_answer = bank_task.answer if bank_task else ""
    solution = bank_task.solution if bank_task else ""

    user_clean = check_in.user_answer.strip().lower().replace(",", ".")
    correct_clean = correct_answer.strip().lower().replace(",", ".")

    is_correct = (user_clean == correct_clean) if correct_clean else True

    if is_correct:
        # Решение принято верно -> Завершаем ДЗ и заявку, начисляем XP обоим!
        tutor_id = task.tutor_id or (task.tutor.id if task.tutor else None)
        if tutor_id:
            await crud_homework.review_solution(
                session=session,
                homework=hw,
                is_accepted=True,
                feedback="Ответ верный! Тема полностью усвоена и закреплена.",
                tutor_id=tutor_id,
            )
        else:
            hw.status = "ACCEPTED"
            task.status = "COMPLETED"
            await session.flush()

        await session.commit()

        # Уведомления обоим
        try:
            if task.tutor:
                topic_title = task.topic.title if task.topic else "Физика (ОГЭ)"
                student_name = task.student.first_name if task.student else "Ученик"
                asyncio.ensure_future(
                    notify_task_completed(
                        tutor_tg_id=task.tutor.telegram_id,
                        task_id=task_id,
                        topic_title=topic_title,
                        student_name=student_name,
                        tutor_xp=150,
                    )
                )
        except Exception:
            pass

        return CheckAnswerResponse(
            is_correct=True,
            correct_answer=correct_answer,
            solution=solution,
            xp_awarded=100,
            message="🎉 Отлично! Ответ верный. Тема полностью закреплена и вопрос успешно закрыт (+100 XP)!",
        )
    else:
        return CheckAnswerResponse(
            is_correct=False,
            correct_answer=None,
            solution=None,
            xp_awarded=0,
            message="❌ Ответ не сошёлся. Проверьте расчеты, формулы и единицы измерения и попробуйте ещё раз!",
        )


@router.post("/tasks/{task_id}/complete", response_model=TaskResponse, summary="Подтвердить, что вопрос решен")
async def complete_task_endpoint(
    task_id: int,
    student_tg_id: Optional[int] = Query(None, description="Telegram ID ученика для уведомления"),
    session: AsyncSession = Depends(get_db),
):
    task = await crud_task.get_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    task, tutor_xp, _ = await crud_task.complete_task(session, task)
    result = await crud_task.get_by_id(session, task.id)

    # Push-уведомление преподавателю о закрытии задачи
    try:
        if result.tutor:
            topic_title = result.topic.title if result.topic else "Физика (ОГЭ)"
            student_name = result.student.first_name if result.student else "Ученик"
            asyncio.ensure_future(
                notify_task_completed(
                    tutor_tg_id=result.tutor.telegram_id,
                    task_id=task_id,
                    topic_title=topic_title,
                    student_name=student_name,
                    tutor_xp=tutor_xp or 100,
                )
            )
    except Exception:
        pass

    return result



# ==========================================
# 4. ДОМАШНЕЕ ЗАДАНИЕ (ФОРМАТ ОГЭ)
# ==========================================
@router.post("/tasks/{task_id}/homework", response_model=HomeworkResponse, summary="Выдать ДЗ формата ОГЭ")
async def issue_homework(
    task_id: int,
    hw_in: HomeworkCreate,
    tutor_tg_id: int = Query(...),
    session: AsyncSession = Depends(get_db),
):
    task = await crud_task.get_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    tutor = await crud_user.get_by_telegram_id(session, tutor_tg_id)
    if not tutor:
        raise HTTPException(status_code=404, detail="Тьютор не найден")

    try:
        return await crud_homework.create(session, task, tutor_id=tutor.id, homework_in=hw_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/homework/{hw_id}/submit", response_model=HomeworkResponse, summary="Ученик сдает фото решения ДЗ")
async def submit_homework(
    hw_id: int,
    submit_in: HomeworkSubmit,
    student_tg_id: int = Query(...),
    session: AsyncSession = Depends(get_db),
):
    homework = await crud_homework.get_by_id(session, hw_id)
    if not homework:
        raise HTTPException(status_code=404, detail="ДЗ не найдено")

    student = await crud_user.get_by_telegram_id(session, student_tg_id)
    if not student:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    try:
        return await crud_homework.submit_solution(
            session=session,
            homework=homework,
            solution_photo_url=submit_in.solution_photo_url,
            student_id=student.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/homework/{hw_id}/review", response_model=HomeworkResponse, summary="Тьютор проверяет ДЗ (Принять / На доработку)")
async def review_homework(
    hw_id: int,
    review_in: HomeworkReview,
    tutor_tg_id: int = Query(...),
    session: AsyncSession = Depends(get_db),
):
    homework = await crud_homework.get_by_id(session, hw_id)
    if not homework:
        raise HTTPException(status_code=404, detail="ДЗ не найдено")

    tutor = await crud_user.get_by_telegram_id(session, tutor_tg_id)
    if not tutor:
        raise HTTPException(status_code=404, detail="Тьютор не найден")

    try:
        hw, _ = await crud_homework.review_solution(
            session=session,
            homework=homework,
            is_accepted=review_in.is_accepted,
            feedback=review_in.feedback,
            tutor_id=tutor.id,
        )
        return hw
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 5. БАНК ЗАДАЧ (ОТКРЫТЫЙ И ЗАКРЫТЫЙ) ДЛЯ FRONTEND
# ==========================================


@router.get(
    "/bank/solved-tasks",
    response_model=List[TaskResponse],
    summary="Получить базу разобранных задач (решённые заявки с методическими ответами и формулами)",
)
async def get_solved_bank_tasks(
    grade: Optional[int] = Query(None, description="Класс: 7, 8, 9"),
    block: Optional[str] = Query(None, description="Раздел: MECHANICS, THERMODYNAMICS, ELECTRODYNAMICS, QUANTUM, PART_2_ADVANCED"),
    topic_id: Optional[int] = Query(None, description="ID темы"),
    search: Optional[str] = Query(None, description="Текстовый поиск по условию, формулам или теме"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    """Возвращает решённые заявки с подробными разборами преподавателей, формулами и фото."""
    return await crud_task.get_solved_tasks(
        session=session,
        grade=grade,
        block=block,
        topic_id=topic_id,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/bank/tasks",
    response_model=List[BankTaskStudentResponse],
    summary="Получить список задач из Открытого банка (для учеников)",
)
async def get_open_bank_tasks(
    grade: Optional[int] = Query(None, description="Класс: 7, 8, 9"),
    block: Optional[str] = Query(None, description="Раздел: MECHANICS, THERMODYNAMICS, ELECTRODYNAMICS, QUANTUM, PART_2_ADVANCED"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    """Возвращает тренировочные задачи из Открытого банка для фронтенда учеников."""
    return await crud_bank_task.get_tasks(
        session=session,
        grade=grade,
        block=block,
        bank_type="OPEN",
        limit=limit,
        offset=offset,
    )


@router.get(
    "/bank/tasks/tutor",
    response_model=List[BankTaskTutorResponse],
    summary="Получить список задач из Закрытого банка (для преподавателей / выдачи ДЗ)",
)
async def get_closed_bank_tasks(
    grade: Optional[int] = Query(None, description="Класс: 7, 8, 9"),
    block: Optional[str] = Query(None, description="Раздел: MECHANICS, THERMODYNAMICS, ELECTRODYNAMICS, QUANTUM, PART_2_ADVANCED"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    """Возвращает задачи из Закрытого банка с эталонными ответами и критериями для преподавателей."""
    return await crud_bank_task.get_tasks(
        session=session,
        grade=grade,
        block=block,
        bank_type="CLOSED",
        limit=limit,
        offset=offset,
    )


@router.get(
    "/bank/tasks/{task_id}",
    response_model=BankTaskStudentResponse,
    summary="Получить карточку одной задачи",
)
async def get_bank_task_by_id(
    task_id: int,
    session: AsyncSession = Depends(get_db),
):
    task = await crud_bank_task.get_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена в банке")
    return task


@router.post(
    "/bank/tasks/{task_id}/check-answer",
    response_model=CheckAnswerResponse,
    summary="Проверить ответ ученика на задачу из банка",
)
async def check_task_answer(
    task_id: int,
    check_in: CheckAnswerRequest,
    session: AsyncSession = Depends(get_db),
):
    task = await crud_bank_task.get_by_id(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    user_clean = check_in.user_answer.strip().lower().replace(",", ".")
    correct_clean = task.answer.strip().lower().replace(",", ".")

    is_correct = (user_clean == correct_clean)
    xp_awarded = 0

    if is_correct:
        if check_in.student_tg_id:
            student = await crud_user.get_by_telegram_id(session, check_in.student_tg_id)
            if student:
                await award_xp(session, user_id=student.id, amount=15, reason=XPReason.BANK_SOLVED.value, task_id=task.id)
                xp_awarded = 15
                await session.commit()

        return CheckAnswerResponse(
            is_correct=True,
            correct_answer=task.answer,
            solution=task.solution,
            xp_awarded=xp_awarded,
            message="🎉 Отлично! Ответ верный. Вам начислено +15 XP!",
        )
    else:
        return CheckAnswerResponse(
            is_correct=False,
            correct_answer=None,
            solution=None,
            xp_awarded=0,
            message="❌ Ответ неверный. Попробуйте еще раз или воспользуйтесь подсказкой.",
        )


@router.post(
    "/bank/assign-homework",
    response_model=HomeworkResponse,
    summary="Преподаватель назначает задачу из закрытого банка в качестве ДЗ",
)
async def assign_closed_bank_task_as_homework(
    req: AssignHomeworkRequest,
    session: AsyncSession = Depends(get_db),
):
    bank_task = await crud_bank_task.get_by_id(session, req.bank_task_id)
    if not bank_task:
        raise HTTPException(status_code=404, detail="Задача из банка не найдена")

    task = await crud_task.get_by_id(session, req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Заявка разбора не найдена")

    tutor = await crud_user.get_by_telegram_id(session, req.tutor_tg_id)
    if not tutor or task.tutor_id != tutor.id:
        raise HTTPException(status_code=403, detail="Вы не являетесь преподавателем по этой задаче")

    hw_text = (
        f"🔒 ДЗ из закрытого банка ({bank_task.grade} класс, {bank_task.difficulty}):\n"
        f"«{bank_task.title}»\n\n"
        f"{bank_task.statement}"
    )

    hw_in = HomeworkCreate(task_text=hw_text)
    hw = await crud_homework.create(
        session=session,
        task=task,
        tutor_id=tutor.id,
        homework_in=hw_in,
        bank_task_id=bank_task.id,
    )

    # Уведомляем ученика о выданной задаче из закрытого банка
    try:
        student_tg_id = task.student.telegram_id if task.student else None
        if student_tg_id:
            topic_title = task.topic.title if task.topic else "Физика (ОГЭ)"
            asyncio.ensure_future(
                notify_homework_issued(
                    student_tg_id=student_tg_id,
                    task_id=task.id,
                    topic_title=topic_title,
                    task_name=bank_task.title,
                )
            )
    except Exception:
        pass

    return hw


@router.get(
    "/bank/stats",
    summary="Статистика банка задач (по классам и разделам)",
)
async def get_bank_stats(
    session: AsyncSession = Depends(get_db),
):
    open_count = await crud_bank_task.count_tasks(session, bank_type="OPEN")
    closed_count = await crud_bank_task.count_tasks(session, bank_type="CLOSED")

    return {
        "total_tasks": open_count + closed_count,
        "open_bank_count": open_count,
        "closed_bank_count": closed_count,
        "grades": [7, 8, 9],
        "blocks": [
            "MECHANICS",
            "THERMODYNAMICS",
            "ELECTRODYNAMICS",
            "QUANTUM",
            "PART_2_ADVANCED",
        ],
    }

