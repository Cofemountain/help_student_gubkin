import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Кодировка UTF-8 для вывода в консоль Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)
from aiogram.client.default import DefaultBotProperties
from sqlalchemy import select

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://135.106.229.213.sslip.io")

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.crud.crud_user import crud_user
from app.crud.crud_topic import crud_topic
from app.crud.crud_task import crud_task
from app.models.user import User, UserRole, OGELevel
from app.models.topic import OGEBlock
from app.models.task import Task, TaskPart, TaskStatus
from app.schemas.user import UserCreate
from app.schemas.task import TaskCreate
from app.services.gamification import award_xp
from app.services.quiz import get_quiz_by_id, get_random_quiz, OGE_QUIZ_TASKS
from scripts.seed_oge_topics import seed_topics

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

dp = Dispatcher(storage=MemoryStorage())

# Папка для сохранения фото задач
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads" / "tasks"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Человекочитаемые названия разделов ОГЭ
BLOCK_NAMES = {
    OGEBlock.MECHANICS.value: "⚙️ Механические явления",
    OGEBlock.THERMODYNAMICS.value: "🔥 Тепловые явления",
    OGEBlock.ELECTRODYNAMICS.value: "⚡️ Электромагнитные явления",
    OGEBlock.QUANTUM.value: "🔬 Квантовые явления",
    OGEBlock.PART_2_ADVANCED.value: "⭐️ Вторая часть (№20–25 ОГЭ)",
}

LEVEL_NAMES = {
    OGELevel.GRADE_3.value: "🥉 Порог сдачи (Оценка 3)",
    OGELevel.GRADE_4.value: "🥈 Уверенная 4-ка (Оценка 4)",
    OGELevel.GRADE_5.value: "🥇 Отличник ОГЭ (Оценка 5)",
}


# ==========================================================
# КЛАВИАТУРЫ
# ==========================================================

def get_main_keyboard(user_role: str) -> ReplyKeyboardMarkup:
    app_role = "teacher" if user_role == UserRole.TUTOR.value else "student"
    webapp_btn = [KeyboardButton(text="🚀 Открыть трекер ОГЭ (Mini App)", web_app=WebAppInfo(url=f"{FRONTEND_URL}/?role={app_role}"))]

    if user_role == UserRole.STUDENT.value:
        kb = [
            webapp_btn,
            [KeyboardButton(text="➕ Разобрать задачу ОГЭ"), KeyboardButton(text="👤 Мой профиль и XP")],
            [KeyboardButton(text="📚 Темы ОГЭ (9 класс)"), KeyboardButton(text="📂 Мои задачи")],
            [KeyboardButton(text="🔄 Переключить на Тьютора"), KeyboardButton(text="ℹ️ Как устроен сервис")],
        ]
    else:
        kb = [
            webapp_btn,
            [KeyboardButton(text="📋 Свободные задачи ОГЭ"), KeyboardButton(text="👤 Мой профиль и XP")],
            [KeyboardButton(text="📚 Темы ОГЭ (9 класс)"), KeyboardButton(text="💼 Мои разборы")],
            [KeyboardButton(text="🔄 Переключить на Ученика"), KeyboardButton(text="ℹ️ Как устроен сервис")],
        ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


# ==========================================================
# FSM: СОСТОЯНИЯ СОЗДАНИЯ ЗАЯВКИ УЧЕНИКОМ
# ==========================================================

class CreateTaskFSM(StatesGroup):
    choose_block = State()     # 1. Выбор раздела ОГЭ
    choose_topic = State()     # 2. Выбор темы
    choose_part = State()      # 3. Выбор части ОГЭ (Часть 1 или 2)
    upload_photo = State()     # 4. Загрузка фото условия
    write_question = State()   # 5. Что конкретно вызвало затык
    set_time = State()         # 6. Удобное время разбора


# ==========================================================
# БАЗОВЫЕ КОМАНДЫ
# ==========================================================

@dp.message(CommandStart())
async def handle_start(message: types.Message, state: FSMContext):
    await state.clear()
    tg_user = message.from_user
    if not tg_user:
        return

    async with AsyncSessionLocal() as session:
        user_in = UserCreate(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        user, is_new = await crud_user.get_or_create(session, user_in)
        await session.commit()

    role_desc = "👨‍🎓 **Ученик (9 класс)**" if user.active_role == "student" else "👨‍🏫 **Тьютор / Наставник**"
    welcome_text = (
        f"👋 Привет, **{tg_user.first_name}**!\n\n"
        f"Добро пожаловать в **ФизPoint** — платформу подготовки к **ОГЭ по физике (9 класс)**! 🎯\n\n"
        f"Твой текущий режим: {role_desc}\n\n"
        f"💡 **Возможности:**\n"
        f"• Нажми **«🚀 Открыть трекер ОГЭ (Mini App)»** ниже или в меню для запуска приложения прямо в Telegram!\n"
        f"• Нажми **«➕ Разобрать задачу ОГЭ»**, чтобы отправить фото сложной задачи тьюторам.\n"
        f"• Нажми **«📋 Свободные задачи ОГЭ»** (в режиме тьютора), чтобы помочь девятиклассникам и получить +XP.\n"
        f"• Прокачивай свой ранг от *«Порога сдачи (3)»* до *«Отличника ОГЭ (5)»*!"
    )

    app_role = "teacher" if user.active_role == UserRole.TUTOR.value else "student"
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Запустить платформу (Mini App)", web_app=WebAppInfo(url=f"{FRONTEND_URL}/?role={app_role}"))]
    ])

    await message.answer(
        welcome_text,
        reply_markup=inline_kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await message.answer(
        "Навигация:",
        reply_markup=get_main_keyboard(user.active_role),
    )


@dp.message(F.text == "❌ Отмена")
@dp.message(Command("cancel"))
async def handle_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, message.from_user.id)
        role = user.active_role if user else UserRole.STUDENT.value

    await message.answer(
        "❌ Действие отменено.",
        reply_markup=get_main_keyboard(role),
    )


# ==========================================================
# ШАГ 1: FSM СОЗДАНИЯ ЗАЯВКИ УЧЕНИКОМ
# ==========================================================

@dp.message(F.text == "➕ Разобрать задачу ОГЭ")
async def start_create_task(message: types.Message, state: FSMContext):
    await state.clear()
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала введите /start")
            return

        # Если пользователь в режиме тьютора, переключаем на ученика для создания
        if user.active_role != UserRole.STUDENT.value:
            await crud_user.update_active_role(session, user, UserRole.STUDENT.value)
            await session.commit()

    # Показываем кнопки выбора раздела ОГЭ
    buttons = []
    for code, title in BLOCK_NAMES.items():
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"block:{code}")])

    ikb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        "📚 **Шаг 1 из 5.** Выберите **раздел физики ОГЭ**, к которому относится задача:",
        reply_markup=ikb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await state.set_state(CreateTaskFSM.choose_block)


@dp.callback_query(CreateTaskFSM.choose_block, F.data.startswith("block:"))
async def on_block_chosen(cb: CallbackQuery, state: FSMContext):
    block_code = cb.data.split(":", 1)[1]
    await state.update_data(chosen_block=block_code)

    # Загружаем темы выбранного раздела
    async with AsyncSessionLocal() as session:
        topics = await crud_topic.get_all(session, block=block_code, is_active=True)

    buttons = []
    for t in topics:
        short_title = t.title if len(t.title) <= 45 else t.title[:42] + "..."
        buttons.append([InlineKeyboardButton(text=f"№{t.sort_order} {short_title}", callback_data=f"topic:{t.id}")])

    ikb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await cb.message.edit_text(
        f"📖 **Шаг 2 из 5.** Раздел: **{BLOCK_NAMES.get(block_code, block_code)}**.\n"
        f"Выберите тему из кодификатора ОГЭ:",
        reply_markup=ikb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await state.set_state(CreateTaskFSM.choose_topic)
    await cb.answer()


@dp.callback_query(CreateTaskFSM.choose_topic, F.data.startswith("topic:"))
async def on_topic_chosen(cb: CallbackQuery, state: FSMContext):
    topic_id = int(cb.data.split(":", 1)[1])
    await state.update_data(chosen_topic_id=topic_id)

    # Выбор части ОГЭ (1 или 2)
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Часть 1 (тест / базовая)", callback_data="part:PART_1"),
            InlineKeyboardButton(text="⭐️ Часть 2 (развернутый ответ)", callback_data="part:PART_2"),
        ]
    ])
    await cb.message.edit_text(
        "🎯 **Шаг 3 из 5.** К какой части ОГЭ относится задача?",
        reply_markup=ikb,
        parse_mode=ParseMode.MARKDOWN,
    )
    await state.set_state(CreateTaskFSM.choose_part)
    await cb.answer()


@dp.callback_query(CreateTaskFSM.choose_part, F.data.startswith("part:"))
async def on_part_chosen(cb: CallbackQuery, state: FSMContext):
    part_val = cb.data.split(":", 1)[1]
    await state.update_data(chosen_part=part_val)

    part_label = "Часть 1 (тестовая)" if part_val == "PART_1" else "Часть 2 (развернутая)"
    await cb.message.edit_text(
        f"✅ Выбрано: **{part_label}**.\n\n"
        f"📸 **Шаг 4 из 5. Прикрепите фотографию условия задачи**.\n"
        f"_(Сфотографируйте страницу сборника, пробника или скриншот)_",
        parse_mode=ParseMode.MARKDOWN,
    )
    await cb.message.answer(
        "Ожидаю фото... Или нажмите «Отмена» внизу 👇",
        reply_markup=get_cancel_keyboard(),
    )
    await state.set_state(CreateTaskFSM.upload_photo)
    await cb.answer()


@dp.message(CreateTaskFSM.upload_photo, F.photo)
async def on_photo_uploaded(message: types.Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1]  # Берем фото в максимальном разрешении
    file_info = await bot.get_file(photo.file_id)

    # Сохраняем локально в папку uploads/tasks/
    filename = f"task_{message.from_user.id}_{int(time.time())}.jpg"
    dest_path = UPLOAD_DIR / filename
    await bot.download_file(file_info.file_path, destination=dest_path)

    rel_path = f"uploads/tasks/{filename}"
    await state.update_data(photo_url=rel_path, photo_file_id=photo.file_id)

    await message.answer(
        "👍 Фотография принята!\n\n"
        "❓ **Шаг 5 из 5.** Напишите кратко: **что конкретно непонятно в задаче?**\n"
        "_(например: «Не понимаю, какую формулу применить» или «Путаюсь в знаках проекций сил»)_",
        reply_markup=get_cancel_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await state.set_state(CreateTaskFSM.write_question)


@dp.message(CreateTaskFSM.upload_photo, ~F.photo)
async def on_photo_not_provided(message: types.Message):
    await message.answer("Пожалуйста, прикрепите именно **фотографию** условия задачи (как фото, не файл).")


@dp.message(CreateTaskFSM.write_question, F.text)
async def on_question_written(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        return
    await state.update_data(question=message.text)

    await message.answer(
        "⏰ **Последний штрих:** Укажите **удобное время для онлайн-разбора**:\n"
        "_(например: «Сегодня в 19:00» или «Завтра после 17:30»)_",
        reply_markup=get_cancel_keyboard(),
        parse_mode=ParseMode.MARKDOWN,
    )
    await state.set_state(CreateTaskFSM.set_time)


@dp.message(CreateTaskFSM.set_time, F.text)
async def on_time_set_and_finish(message: types.Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Отмена":
        return

    scheduled_time = message.text
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Ошибка: пользователь не найден.")
            return

        task_in = TaskCreate(
            topic_id=data["chosen_topic_id"],
            part=data["chosen_part"],
            photo_url=data["photo_url"],
            question=data["question"],
            scheduled_time=scheduled_time,
        )
        task = await crud_task.create(session, student_id=user.id, task_in=task_in)
        await session.commit()
        await session.refresh(user)

        # Получаем данные о теме для уведомления
        topic = await crud_topic.get_by_id(session, task.topic_id)
        topic_title = topic.title if topic else "Тема ОГЭ"
        part_name = "Часть 1 (тестовая)" if task.part == "PART_1" else "Часть 2 (развернутый ответ)"

        # Ищем тьюторов для рассылки пуша о новой задаче
        tutors_res = await session.execute(
            select(User).where(User.active_role == UserRole.TUTOR.value)
        )
        tutors = list(tutors_res.scalars().all())

    # Сообщение ученику об успешной публикации
    success_text = (
        f"🎉 **Заявка #{task.id} успешно опубликована на доске ОГЭ!**\n\n"
        f"• **Тема:** {topic_title}\n"
        f"• **Уровень:** {part_name}\n"
        f"• **Вопрос:** _{task.question}_\n"
        f"• **Желаемое время:** {task.scheduled_time}\n\n"
        f"🏆 Твой баланс: **{user.xp} XP** (начислено +50 XP за дебютную заявку!)\n"
        f"Тьюторы уже получили уведомление. Как только кто-то возьмет задачу, тебе придет мгновенный пуш!"
    )
    await message.answer(
        success_text,
        reply_markup=get_main_keyboard(UserRole.STUDENT.value),
        parse_mode=ParseMode.MARKDOWN,
    )

    # Оповещаем всех тьюторов
    tutor_notify_text = (
        f"🔔 **Новая задача ОГЭ ждет разбора!** (Заявка #{task.id})\n\n"
        f"• **Тема:** {topic_title}\n"
        f"• **Часть:** {part_name}\n"
        f"• **Ученик:** {message.from_user.first_name}\n"
        f"• **Вопрос:** _{task.question}_\n"
        f"• **Время:** {task.scheduled_time}"
    )
    accept_ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤝 Помочь разобрать (+100 XP)", callback_data=f"accept:{task.id}")]
    ])

    for tutor in tutors:
        # Не шлем автору задачи
        if tutor.telegram_id == message.from_user.id:
            continue
        try:
            if "photo_file_id" in data:
                await bot.send_photo(
                    chat_id=tutor.telegram_id,
                    photo=data["photo_file_id"],
                    caption=tutor_notify_text,
                    reply_markup=accept_ikb,
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                await bot.send_message(
                    chat_id=tutor.telegram_id,
                    text=tutor_notify_text,
                    reply_markup=accept_ikb,
                    parse_mode=ParseMode.MARKDOWN,
                )
        except Exception as e:
            logger.warning(f"Не удалось отправить уведомление тьютору {tutor.telegram_id}: {e}")


# ==========================================================
# ШАГ 2: ДОСКА ЗАДАЧ ДЛЯ ТЬЮТОРОВ И ОТКЛИК («ПОМОЧЬ»)
# ==========================================================

@dp.message(F.text == "📋 Свободные задачи ОГЭ")
async def show_tutor_board(message: types.Message, bot: Bot):
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала введите /start")
            return

        open_tasks = await crud_task.get_board_tasks(session, status=TaskStatus.OPEN.value)

    if not open_tasks:
        await message.answer(
            "✨ **На доске пока нет свободных задач.**\n"
            "Как только девятиклассники опубликуют новый вопрос, бот сразу пришлет вам пуш!",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await message.answer(f"📋 **Свободные задачи ОГЭ на доске (всего: {len(open_tasks)}):**")

    # Показываем карточки задач (до 5 последних)
    for task in open_tasks[:5]:
        part_str = "Часть 1 (тестовая)" if task.part == "PART_1" else "⭐️ Часть 2 (развернутая)"
        topic_title = task.topic.title if task.topic else "Тема ОГЭ"
        author_name = task.student.first_name if task.student else "Ученик"

        card_text = (
            f"📌 **Задача #{task.id}** ({part_str})\n"
            f"• **Тема:** {topic_title}\n"
            f"• **Ученик:** {author_name}\n"
            f"• **Вопрос:** _{task.question}_\n"
            f"• **Время созвона:** {task.scheduled_time}\n"
            f"• **Награда:** `+100 XP` за разбор"
        )
        ikb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤝 Помочь разобрать", callback_data=f"accept:{task.id}")]
        ])

        # Проверяем наличие файла фото на диске
        photo_path = Path(__file__).resolve().parent / task.photo_url
        if photo_path.exists():
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=FSInputFile(str(photo_path)),
                caption=card_text,
                reply_markup=ikb,
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await message.answer(card_text, reply_markup=ikb, parse_mode=ParseMode.MARKDOWN)


@dp.callback_query(F.data.startswith("accept:"))
async def on_task_accepted_by_tutor(cb: CallbackQuery, bot: Bot):
    task_id = int(cb.data.split(":", 1)[1])
    tutor_tg = cb.from_user

    async with AsyncSessionLocal() as session:
        tutor = await crud_user.get_by_telegram_id(session, tutor_tg.id)
        if not tutor:
            await cb.answer("Сначала введите /start", show_alert=True)
            return

        task = await crud_task.get_by_id(session, task_id)
        if not task:
            await cb.answer("Задача не найдена или уже удалена.", show_alert=True)
            return

        if task.status != TaskStatus.OPEN.value:
            await cb.answer("Эту задачу уже взял другой тьютор!", show_alert=True)
            return

        if task.student_id == tutor.id:
            await cb.answer("Вы не можете взять свою собственную задачу!", show_alert=True)
            return

        # Переводим в IN_PROGRESS
        await crud_task.accept_task(session, task, tutor_id=tutor.id)
        await session.commit()

        # Данные автора для уведомления
        student = task.student
        student_tg_id = student.telegram_id if student else None
        scheduled_time = task.scheduled_time
        topic_title = task.topic.title if task.topic else "Задача ОГЭ"

    # Ответ тьютору
    tutor_confirm = (
        f"✅ **Вы взяли задачу #{task_id} в работу!**\n\n"
        f"• **Тема:** {topic_title}\n"
        f"• **Время созвона:** {scheduled_time}\n"
        f"• **Ученик:** {student.first_name} (@{student.username or 'без_юзернейма'})\n\n"
        f"Свяжитесь с учеником в Telegram для проведения консультации."
    )
    if cb.message.caption:
        await cb.message.edit_caption(caption=tutor_confirm, parse_mode=ParseMode.MARKDOWN)
    else:
        await cb.message.edit_text(text=tutor_confirm, parse_mode=ParseMode.MARKDOWN)

    await cb.answer("Задача взята в работу!", show_alert=False)

    # МГНОВЕННЫЙ ПУШ УЧЕНИКУ!
    if student_tg_id:
        tutor_username = f"@{tutor_tg.username}" if tutor_tg.username else tutor_tg.first_name
        push_to_student = (
            f"⚡️ **Отличные новости по задаче #{task_id}!**\n\n"
            f"Тьютор **{tutor_tg.first_name}** ({tutor_username}) взял твою задачу на разбор!\n\n"
            f"• **Тема:** {topic_title}\n"
            f"• **Время разбора:** {scheduled_time}\n"
            f"• **Контакт тьютора:** {tutor_username}\n\n"
            f"Напиши тьютору или ожидай сообщения для созвона! 🚀"
        )
        try:
            await bot.send_message(
                chat_id=student_tg_id,
                text=push_to_student,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            logger.error(f"Не удалось отправить пуш ученику {student_tg_id}: {e}")


# ==========================================================
# ПРОСМОТР МОИХ ЗАДАЧ (УЧЕНИК / ТЬЮТОР)
# ==========================================================

@dp.message(F.text == "📂 Мои задачи")
async def show_my_student_tasks(message: types.Message):
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала введите /start")
            return
        tasks = await crud_task.get_student_tasks(session, student_id=user.id)

    if not tasks:
        await message.answer("У вас пока нет созданных задач. Нажмите **«➕ Разобрать задачу ОГЭ»**!")
        return

    status_labels = {
        "OPEN": "🟡 Поиск тьютора",
        "IN_PROGRESS": "🔵 В работе (назначен разбор)",
        "HW_SUBMITTED": "🟣 ДЗ на проверке",
        "COMPLETED": "🟢 Завершено (+100 XP)",
    }

    lines = [f"📂 **Ваши задачи ОГЭ (всего: {len(tasks)}):**\n"]
    for t in tasks[:7]:
        st = status_labels.get(t.status, t.status)
        t_name = t.topic.title[:35] if t.topic else "Тема"
        lines.append(f"• `#{t.id}` | {st} | **{t_name}** (Время: {t.scheduled_time})")

    await message.answer("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


@dp.message(F.text == "💼 Мои разборы")
async def show_my_tutor_sessions(message: types.Message):
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала введите /start")
            return
        tasks = await crud_task.get_tutor_tasks(session, tutor_id=user.id)

    if not tasks:
        await message.answer("У вас пока нет взятых задач. Откройте **«📋 Свободные задачи ОГЭ»**!")
        return

    lines = [f"💼 **Ваши текущие разборы (всего: {len(tasks)}):**\n"]
    for t in tasks[:7]:
        st = "🔵 В работе" if t.status == "IN_PROGRESS" else t.status
        s_name = t.student.first_name if t.student else "Ученик"
        lines.append(f"• `#{t.id}` | {st} | Ученик: {s_name} | {t.scheduled_time}")

    await message.answer("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


# ==========================================================
# ПРОФИЛЬ, ТЕМЫ И ПЕРЕКЛЮЧАТЕЛЬ РОЛЕЙ
# ==========================================================

@dp.message(F.text == "👤 Мой профиль и XP")
async def handle_profile(message: types.Message):
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Пользователь не найден. Введите /start")
            return

        lvl_name = LEVEL_NAMES.get(user.level, user.level)
        next_goal = ""
        if user.xp < 201:
            next_goal = f"🎯 До ранга «Уверенная 4-ка»: осталось **{201 - user.xp} XP**"
        elif user.xp < 600:
            next_goal = f"🎯 До ранга «Отличник ОГЭ (5)»: осталось **{600 - user.xp} XP**"
        else:
            next_goal = "🏆 Вы достигли высшего ранга «Отличник ОГЭ»!"

        profile_text = (
            f"👤 **Твой профиль ОГЭ:**\n\n"
            f"• **Имя:** {user.first_name} {user.last_name or ''}\n"
            f"• **Роль:** {'👨‍🎓 Ученик (сдаю ОГЭ)' if user.active_role == 'student' else '👨‍🏫 Тьютор (помогаю)'}\n"
            f"• **Очки опыта:** `{user.xp} XP`\n"
            f"• **Текущий ранг:** {lvl_name}\n\n"
            f"{next_goal}\n\n"
            f"💎 *Начисление XP: +50 за первую задачу, +100 за принятое ДЗ, +100 тьютору за разбор.*"
        )
        await message.answer(profile_text, parse_mode=ParseMode.MARKDOWN)


@dp.message(F.text == "📚 Темы ОГЭ (9 класс)")
async def handle_topics(message: types.Message):
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Случайная задача (+1 XP)", callback_data="quiz_rnd")],
        [
            InlineKeyboardButton(text="⚙️ Механика", callback_data=f"quiz_block:{OGEBlock.MECHANICS.value}"),
            InlineKeyboardButton(text="🔥 Теплота", callback_data=f"quiz_block:{OGEBlock.THERMODYNAMICS.value}"),
        ],
        [
            InlineKeyboardButton(text="⚡️ Электричество", callback_data=f"quiz_block:{OGEBlock.ELECTRODYNAMICS.value}"),
            InlineKeyboardButton(text="🔬 Кванты", callback_data=f"quiz_block:{OGEBlock.QUANTUM.value}"),
        ],
        [InlineKeyboardButton(text="⭐️ Задача 2-й части (№21 ОГЭ)", callback_data=f"quiz_block:{OGEBlock.PART_2_ADVANCED.value}")],
        [InlineKeyboardButton(text="📋 Полный список всех 17 тем ФИПИ", callback_data="topics_full_list")],
    ])

    text = (
        "📚 **Кодификатор и Тренажер задач ОГЭ (9 класс)**\n\n"
        "💡 **Выберите режим:**\n"
        "• **🎯 Решать задачи:** тренируйтесь прямо в боте. За каждый правильный ответ начисляется **+1 XP** активности!\n"
        "• **📋 Темы:** просмотрите все темы программы ОГЭ по 5 разделам."
    )
    await message.answer(text, reply_markup=ikb, parse_mode=ParseMode.MARKDOWN)


@dp.callback_query(F.data.startswith("quiz_block:") | (F.data == "quiz_rnd"))
async def handle_quiz_start(cb: CallbackQuery):
    block = None
    if cb.data.startswith("quiz_block:"):
        block = cb.data.split(":", 1)[1]

    quiz = get_random_quiz(block)
    if not quiz:
        await cb.answer("Задачи в этом разделе временно не найдены.", show_alert=True)
        return

    # Формируем кнопки вариантов ответов (по 2 в ряд)
    options_buttons = []
    row = []
    letters = ["А", "Б", "В", "Г"]
    for idx, opt in enumerate(quiz["options"]):
        btn_text = f"{letters[idx]}) {opt}"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"quiz_ans:{quiz['id']}:{idx}"))
        if len(row) == 2:
            options_buttons.append(row)
            row = []
    if row:
        options_buttons.append(row)

    options_buttons.append([
        InlineKeyboardButton(text="➡️ Другая задача", callback_data="quiz_rnd"),
        InlineKeyboardButton(text="🔙 Меню тем", callback_data="topics_menu"),
    ])

    block_name = BLOCK_NAMES.get(quiz["block"], quiz["block"])
    quiz_text = (
        f"🎯 **Тренажер ОГЭ: {block_name}**\n"
        f"📖 _Тема: {quiz['topic']}_\n\n"
        f"❓ **Вопрос:**\n{quiz['question']}\n\n"
        f"👇 **Выберите правильный вариант (награда: +1 XP):**"
    )

    await cb.message.edit_text(
        quiz_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=options_buttons),
        parse_mode=ParseMode.MARKDOWN,
    )
    await cb.answer()


@dp.callback_query(F.data.startswith("quiz_ans:"))
async def handle_quiz_answer(cb: CallbackQuery):
    parts = cb.data.split(":")
    quiz_id = int(parts[1])
    selected_idx = int(parts[2])

    quiz = get_quiz_by_id(quiz_id)
    if not quiz:
        await cb.answer("Задача устарела.", show_alert=True)
        return

    is_correct = (selected_idx == quiz["correct"])
    letters = ["А", "Б", "В", "Г"]
    correct_letter = letters[quiz["correct"]]
    correct_text = quiz["options"][quiz["correct"]]

    if is_correct:
        # Начисляем +1 XP за решение задачи
        async with AsyncSessionLocal() as session:
            user = await crud_user.get_by_telegram_id(session, cb.from_user.id)
            if user:
                awarded, new_xp, new_lvl = await award_xp(
                    session=session,
                    user_id=user.id,
                    amount=1,
                    reason=f"QUIZ_{quiz['id']}",
                )
                await session.commit()
            else:
                awarded, new_xp = False, 0

        xp_msg = "💎 **+1 XP активности начислено в твой профиль!**" if awarded else "*(Очки за эту задачу уже были начислены ранее)*"

        res_text = (
            f"✅ **Абсолютно верно!** Ответ: **{correct_letter}) {correct_text}**\n\n"
            f"{xp_msg}\n"
            f"Текущий баланс: `{new_xp} XP`\n\n"
            f"{quiz['explanation']}"
        )
        ikb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Следующая задача (+1 XP)", callback_data="quiz_rnd")],
            [InlineKeyboardButton(text="🔙 Меню тем и тренажера", callback_data="topics_menu")],
        ])
    else:
        selected_text = quiz["options"][selected_idx]
        res_text = (
            f"❌ **Неверно!** Вы выбрали: _{selected_text}_\n\n"
            f"Попробуйте подумать еще раз или откройте подробный разбор решения с формулой."
        )
        ikb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💡 Показать разбор и формулу", callback_data=f"quiz_reveal:{quiz['id']}")],
            [InlineKeyboardButton(text="🔄 Другая задача", callback_data="quiz_rnd")],
            [InlineKeyboardButton(text="🔙 Меню тем", callback_data="topics_menu")],
        ])

    await cb.message.edit_text(res_text, reply_markup=ikb, parse_mode=ParseMode.MARKDOWN)
    await cb.answer()


@dp.callback_query(F.data.startswith("quiz_reveal:"))
async def handle_quiz_reveal(cb: CallbackQuery):
    quiz_id = int(cb.data.split(":", 1)[1])
    quiz = get_quiz_by_id(quiz_id)
    if not quiz:
        await cb.answer()
        return

    letters = ["А", "Б", "В", "Г"]
    correct_letter = letters[quiz["correct"]]
    correct_text = quiz["options"][quiz["correct"]]

    reveal_text = (
        f"📖 **Правильный ответ:** **{correct_letter}) {correct_text}**\n\n"
        f"{quiz['explanation']}\n\n"
        f"Закрепите материал на следующей задаче 👇"
    )
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Следующая задача (+1 XP)", callback_data="quiz_rnd")],
        [InlineKeyboardButton(text="🔙 Меню тем", callback_data="topics_menu")],
    ])
    await cb.message.edit_text(reveal_text, reply_markup=ikb, parse_mode=ParseMode.MARKDOWN)
    await cb.answer()


@dp.callback_query(F.data == "topics_menu")
async def handle_topics_menu(cb: CallbackQuery):
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Случайная задача (+1 XP)", callback_data="quiz_rnd")],
        [
            InlineKeyboardButton(text="⚙️ Механика", callback_data=f"quiz_block:{OGEBlock.MECHANICS.value}"),
            InlineKeyboardButton(text="🔥 Теплота", callback_data=f"quiz_block:{OGEBlock.THERMODYNAMICS.value}"),
        ],
        [
            InlineKeyboardButton(text="⚡️ Электричество", callback_data=f"quiz_block:{OGEBlock.ELECTRODYNAMICS.value}"),
            InlineKeyboardButton(text="🔬 Кванты", callback_data=f"quiz_block:{OGEBlock.QUANTUM.value}"),
        ],
        [InlineKeyboardButton(text="⭐️ Задача 2-й части (№21 ОГЭ)", callback_data=f"quiz_block:{OGEBlock.PART_2_ADVANCED.value}")],
        [InlineKeyboardButton(text="📋 Полный список всех 17 тем ФИПИ", callback_data="topics_full_list")],
    ])
    text = (
        "📚 **Кодификатор и Тренажер задач ОГЭ (9 класс)**\n\n"
        "💡 **Выберите режим:**\n"
        "• **🎯 Решать задачи:** тренируйтесь прямо в боте. За каждый правильный ответ начисляется **+1 XP** активности!\n"
        "• **📋 Темы:** просмотрите все темы программы ОГЭ по 5 разделам."
    )
    await cb.message.edit_text(text, reply_markup=ikb, parse_mode=ParseMode.MARKDOWN)
    await cb.answer()


@dp.callback_query(F.data == "topics_full_list")
async def handle_topics_full_list(cb: CallbackQuery):
    async with AsyncSessionLocal() as session:
        topics = await crud_topic.get_all(session, is_active=True)

    current_block = ""
    lines = ["📋 **Кодификатор тем ОГЭ по физике (ФИПИ, 9 класс):**\n"]
    for t in topics:
        if t.block != current_block:
            current_block = t.block
            header = BLOCK_NAMES.get(current_block, current_block)
            lines.append(f"\n__{header}__")
        lines.append(f"• `{t.sort_order}.` {t.title}")

    lines.append("\n_Нажмите кнопку ниже, чтобы перейти к тренировке задач 👇_")
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Потренироваться в задачах (+1 XP)", callback_data="quiz_rnd")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="topics_menu")],
    ])

    await cb.message.edit_text("\n".join(lines), reply_markup=ikb, parse_mode=ParseMode.MARKDOWN)
    await cb.answer()


@dp.message(F.text.startswith("🔄 Переключить"))
async def handle_role_switch(message: types.Message):
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала введите /start")
            return

        new_role = UserRole.TUTOR.value if user.active_role == UserRole.STUDENT.value else UserRole.STUDENT.value
        await crud_user.update_active_role(session, user, new_role)
        await session.commit()

        role_label = "👨‍🏫 Тьютор / Наставник" if new_role == "tutor" else "👨‍🎓 Ученик 9 класса"
        await message.answer(
            f"✅ Режим изменен на: **{role_label}**\nКлавиатура и доступные действия обновлены.",
            reply_markup=get_main_keyboard(new_role),
            parse_mode=ParseMode.MARKDOWN,
        )


@dp.message(F.text == "ℹ️ Как устроен сервис")
async def handle_info(message: types.Message):
    info_text = (
        "ℹ️ **Как работает ФизPoint (ОГЭ 9 класс):**\n\n"
        "1. **Ученик** жмет «➕ Разобрать задачу ОГЭ», выбирает тему и прикрепляет фото условия.\n"
        "2. **Тьюторы** получают уведомление, смотрят задачу на доске и жмут «🤝 Помочь разобрать».\n"
        "3. Стороны созваниваются в удобное время и разбирают сложный момент.\n"
        "4. После разбора тьютор высылает аналогичную задачу на дом.\n"
        "5. Ученик сдает фото решения по критериям ФИПИ и получает **+100 XP**, повышая свой ранг к ОГЭ!"
    )
    await message.answer(info_text, parse_mode=ParseMode.MARKDOWN)


# ==========================================================
# ТОЧКА ВХОДА БОТА
# ==========================================================

async def main():
    token = settings.BOT_TOKEN
    if not token or token == "your_bot_token_here" or len(token) < 20:
        print("\n" + "!" * 70)
        print("❌ ОШИБКА: Токен Telegram-бота не указан в файле .env!")
        print("!" * 70 + "\n")
        return

    # Инициализация БД и сида
    await seed_topics()

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print("\n" + "=" * 60)
    print("🤖 TELEGRAM БОТ ЗАПУЩЕН С ПОЛНЫМ FSM-СЦЕНАРИЕМ И ДОСКОЙ ТЬЮТОРА!")
    print("Откройте бота в Telegram и отправьте /start")
    print("=" * 60 + "\n")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
