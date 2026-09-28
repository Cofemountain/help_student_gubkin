import asyncio
import sys
from pathlib import Path

# Кодировка вывода для Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.database import AsyncSessionLocal, Base, engine
from app.crud.crud_user import crud_user
from app.crud.crud_topic import crud_topic
from app.crud.crud_task import crud_task
from app.crud.crud_homework import crud_homework
from app.models.user import UserRole, OGELevel
from app.models.topic import OGEBlock
from app.models.task import TaskPart, TaskStatus
from app.models.homework import HomeworkStatus
from app.models.xp_transaction import XPReason
from app.schemas.user import UserCreate
from app.schemas.task import TaskCreate
from app.schemas.homework import HomeworkCreate
from app.services.gamification import award_xp
from scripts.seed_oge_topics import seed_topics


async def run_end_to_end_test():
    print("=" * 60)
    print("🚀 СТАРТ СКВОЗНОГО ТЕСТИРОВАНИЯ БАЗЫ ДАННЫХ И СЦЕНАРИЕВ ОГЭ")
    print("=" * 60)

    # 1. Инициализация схемы и сид тем ОГЭ
    await seed_topics()

    async with AsyncSessionLocal() as session:
        # 2. Проверка справочника тем
        all_topics = await crud_topic.get_all(session)
        print(f"\n[1] Проверка тем ОГЭ: всего загружено {len(all_topics)} тем.")
        assert len(all_topics) == 17, f"Ожидалось 17 тем, получено {len(all_topics)}"

        part2_topics = await crud_topic.get_all(session, block=OGEBlock.PART_2_ADVANCED.value)
        print(f"    Тем в блоке 'Вторая часть (№20–25 ОГЭ)': {len(part2_topics)}")
        assert len(part2_topics) == 2
        selected_topic = part2_topics[1]  # Задача №23-25

        # 3. Регистрация / получение пользователей
        student_data = UserCreate(
            telegram_id=777001,
            username="ivan_student_9",
            first_name="Иван",
            last_name="Смирнов",
        )
        tutor_data = UserCreate(
            telegram_id=777002,
            username="alex_phys_tutor",
            first_name="Алексей",
            last_name="Преподавателев",
        )

        student, _ = await crud_user.get_or_create(session, student_data, base_role=UserRole.STUDENT.value)
        tutor, _ = await crud_user.get_or_create(session, tutor_data, base_role=UserRole.TUTOR.value)
        print(f"\n[2] Пользователи:")
        print(f"    Ученик: {student.first_name} (TG: {student.telegram_id}), XP: {student.xp}, Уровень: {student.level}")
        print(f"    Тьютор: {tutor.first_name} (TG: {tutor.telegram_id}), XP: {tutor.xp}, Уровень: {tutor.level}")

        # 4. Ученик публикует заявку ОГЭ (Часть 2)
        task_in = TaskCreate(
            topic_id=selected_topic.id,
            part=TaskPart.PART_2.value,
            photo_url="uploads/tasks/variant4_task24.png",
            question="Не могу составить систему уравнений для расчета КПД наклонной плоскости",
            scheduled_time="Сегодня в 19:00",
        )
        task = await crud_task.create(session, student_id=student.id, task_in=task_in)
        await session.refresh(student)

        print(f"\n[3] Создана заявка #{task.id}:")
        print(f"    Тема: {task.topic.title}")
        print(f"    Часть ОГЭ: {task.part}, Статус: {task.status}")
        print(f"    XP ученика после создания первой заявки: {student.xp} (начислено +50 XP за дебют)")
        assert task.status == TaskStatus.OPEN.value
        assert student.xp == 50

        # 5. Тьютор открывает доску и фильтрует по разделу
        board_tasks = await crud_task.get_board_tasks(
            session,
            status=TaskStatus.OPEN.value,
            block=OGEBlock.PART_2_ADVANCED.value,
        )
        print(f"\n[4] Доска задач тьютора (фильтр: Вторая часть ОГЭ):")
        print(f"    Найдено открытых задач: {len(board_tasks)}")
        assert any(t.id == task.id for t in board_tasks)

        # 6. Тьютор берет задачу в работу
        task = await crud_task.accept_task(session, task, tutor_id=tutor.id)
        print(f"\n[5] Тьютор взял задачу в работу:")
        print(f"    Новый статус задачи: {task.status}, Назначен тьютор id={task.tutor_id}")
        assert task.status == TaskStatus.IN_PROGRESS.value
        assert task.tutor_id == tutor.id

        # 7. После созвона тьютор выдает ДЗ формата ОГЭ
        hw_in = HomeworkCreate(
            task_text="Решить аналогичную комбинированную задачу №24 из открытого банка ФИПИ на КПД",
            task_photo_url="uploads/homeworks/hw_task24_fipi.png",
        )
        homework = await crud_homework.create(
            session=session,
            task=task,
            tutor_id=tutor.id,
            homework_in=hw_in,
        )
        print(f"\n[6] Тьютор выдал ДЗ #{homework.id}:")
        print(f"    Текст ДЗ: '{homework.task_text}'")
        print(f"    Статус ДЗ: {homework.status}")
        assert homework.status == HomeworkStatus.ISSUED.value

        # 8. Ученик сдает фото решения
        homework = await crud_homework.submit_solution(
            session=session,
            homework=homework,
            solution_photo_url="uploads/solutions/ivan_sol_task24.png",
            student_id=student.id,
        )
        task = await crud_task.get_by_id(session, task.id)
        print(f"\n[7] Ученик прикрепил решение:")
        print(f"    Статус ДЗ: {homework.status}, Статус задачи: {task.status}")
        assert homework.status == HomeworkStatus.SUBMITTED.value
        assert task.status == TaskStatus.HW_SUBMITTED.value

        # 9. Тьютор проверяет решение и нажимает «Принять»
        homework, task = await crud_homework.review_solution(
            session=session,
            homework=homework,
            is_accepted=True,
            feedback="Отличное оформление: дано, перевод в СИ и пояснения законов идеальные. Максимальные 3 балла за задачу!",
            tutor_id=tutor.id,
        )
        await session.commit()

        # Обновляем профили после начисления очков
        await session.refresh(student)
        await session.refresh(tutor)

        print(f"\n[8] Тьютор принял ДЗ. Результат проверки:")
        print(f"    Статус ДЗ: {homework.status}, Статус задачи: {task.status}")
        print(f"    Отзыв тьютора: '{homework.feedback}'")
        print(f"    Итоговые очки ученика: {student.xp} XP (+50 старт + 100 за ДЗ), Ранг: {student.level}")
        print(f"    Итоговые очки тьютора: {tutor.xp} XP (+100 за разбор + 50 за проверку ДЗ), Ранг: {tutor.level}")
        assert task.status == TaskStatus.COMPLETED.value
        assert homework.status == HomeworkStatus.ACCEPTED.value
        assert student.xp == 150
        assert tutor.xp == 150

        # 10. Проверка повышения ранга (Level Up до Отличника ОГЭ)
        print(f"\n[9] Тестирование перехода на уровень 'Отличник ОГЭ (Оценка 5)':")
        success, new_xp, new_lvl = await award_xp(
            session=session,
            user_id=student.id,
            amount=500,
            reason="BONUS_STREAK",
        )
        await session.commit()
        await session.refresh(student)
        print(f"    Начислено бонусных очков: +500 XP")
        print(f"    Новый суммарный баланс: {student.xp} XP")
        print(f"    Новый ранг ученика: {student.level} ({OGELevel.GRADE_5.value} = Отличник ОГЭ)")
        assert student.xp == 650
        assert student.level == OGELevel.GRADE_5.value

        # 11. Проверка защиты от дублирования очков (идемпотентность)
        print(f"\n[10] Проверка защиты от повторного начисления очков (идемпотентность):")
        dup_success, _, _ = await award_xp(
            session=session,
            user_id=student.id,
            amount=100,
            reason=XPReason.HW_SOLVED.value,
            task_id=task.id,
        )
        print(f"    Попытка повторного начисления за то же самое ДЗ: success = {dup_success}")
        assert dup_success is False, "Повторное начисление должно быть заблокировано уникальным индексом"

    print("\n" + "=" * 60)
    print("🎉 ВСЕ ТЕСТЫ СЛОЯ БАЗЫ ДАННЫХ И СЦЕНАРИЕВ ОГЭ УСПЕШНО ПРОЙДЕНЫ!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_end_to_end_test())
