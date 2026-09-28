import asyncio
import sys
from pathlib import Path

# Кодировка вывода для Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import AsyncSessionLocal
from app.crud.crud_user import crud_user
from app.crud.crud_topic import crud_topic
from app.crud.crud_task import crud_task
from app.models.user import UserRole
from app.models.task import TaskStatus, TaskPart
from app.schemas.user import UserCreate
from app.schemas.task import TaskCreate
from app.services.gamification import get_user_title
from scripts.seed_oge_topics import seed_topics


async def test_mutual_contact_exchange_flow():
    print("=" * 60)
    print("🧪 ТЕСТ: Взаимный обмен контактами и завершение 'Вопрос решен'")
    print("=" * 60)

    await seed_topics()

    async with AsyncSessionLocal() as session:
        # 1. Получаем тему
        topics = await crud_topic.get_all(session)
        assert len(topics) > 0
        topic = topics[0]

        # 2. Создаем ученика и преподавателя
        student_data = UserCreate(
            telegram_id=99001,
            username="maria_student",
            first_name="Мария",
            last_name="Смирнова",
        )
        tutor_data = UserCreate(
            telegram_id=99002,
            username="alexey_physics",
            first_name="Алексей",
            last_name="Петров",
        )

        student, _ = await crud_user.get_or_create(session, student_data, base_role=UserRole.STUDENT.value)
        tutor, _ = await crud_user.get_or_create(session, tutor_data, base_role=UserRole.TUTOR.value)
        await session.commit()
        await session.refresh(student)
        await session.refresh(tutor)

        print(f"✅ Пользователи зарегистрированы:")
        print(f"   Ученик: {student.first_name} (@{student.username}) ID={student.id}")
        print(f"   Преподаватель: {tutor.first_name} (@{tutor.username}) ID={tutor.id}")

        # 3. Ученик создает заявку
        task_in = TaskCreate(
            topic_id=topic.id,
            part=TaskPart.PART_1.value,
            photo_url="uploads/tasks/demo_task.jpg",
            question="Помогите разобраться с силой Архимеда в сообщающихся сосудах",
            scheduled_time="Сегодня в 19:30",
        )
        task = await crud_task.create(session, student_id=student.id, task_in=task_in)
        await session.commit()
        print(f"\n✅ Заявка #{task.id} создана со статусом {task.status}")
        assert task.status == TaskStatus.OPEN.value

        # 4. Преподаватель нажимает «Взять задачу»
        task = await crud_task.accept_task(session, task, tutor_id=tutor.id)
        await session.commit()
        print(f"✅ Преподаватель взял задачу в работу:")
        print(f"   Новый статус: {task.status}")
        print(f"   Контакты для преподавателя: @{student.username} (https://max.ru/{student.username})")
        print(f"   Контакты для ученика: @{tutor.username} (https://max.ru/{tutor.username})")
        assert task.status == TaskStatus.IN_PROGRESS.value
        assert task.tutor_id == tutor.id

        # 5. Ученик нажимает «Вопрос решен»
        task, tutor_xp, tutor_level = await crud_task.complete_task(session, task)
        await session.commit()
        await session.refresh(student)
        await session.refresh(tutor)

        tutor_title_info = get_user_title("tutor", tutor.xp)
        student_title_info = get_user_title("student", student.xp)

        print(f"\n✅ Ученик нажал «Вопрос решен»:")
        print(f"   Итоговый статус задачи: {task.status}")
        print(f"   Очки преподавателя: {tutor.xp} XP (+100 XP за помощь)")
        print(f"   Звание преподавателя: {tutor_title_info['full_title']}")
        print(f"   Очки ученика: {student.xp} XP")
        print(f"   Звание ученика: {student_title_info['full_title']}")

        assert task.status == TaskStatus.COMPLETED.value
        assert tutor.xp >= 100
        print("\n🎉 Все проверки успешно пройдены!")


if __name__ == "__main__":
    asyncio.run(test_mutual_contact_exchange_flow())
