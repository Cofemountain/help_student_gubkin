import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Настройка UTF-8 вывода для Windows консоли
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

import aiohttp
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.crud.crud_user import crud_user
from app.crud.crud_topic import crud_topic
from app.crud.crud_task import crud_task
from app.crud.crud_bank_task import crud_bank_task
from app.crud.crud_homework import crud_homework
from app.models.user import User, UserRole
from app.models.task import Task, TaskPart, TaskStatus
from app.models.topic import OGEBlock
from app.models.bank_task import BankTask, BankType
from app.models.xp_transaction import XPReason
from app.schemas.user import UserCreate
from app.schemas.task import TaskCreate
from app.schemas.homework import HomeworkCreate
from app.services.gamification import get_user_title, award_xp
from scripts.seed_oge_topics import seed_topics
from scripts.seed_bank_tasks import seed_bank_tasks

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MAX_BOT")

MAX_API_BASE = "https://platform-api2.max.ru"

BLOCK_NAMES = {
    OGEBlock.MECHANICS.value: "⚙️ Механические явления (7-9 кл)",
    OGEBlock.THERMODYNAMICS.value: "🔥 Тепловые явления (8 кл)",
    OGEBlock.ELECTRODYNAMICS.value: "⚡️ Электромагнитные явления (8-9 кл)",
    OGEBlock.QUANTUM.value: "🔬 Квантовые явления (9 кл)",
    OGEBlock.PART_2_ADVANCED.value: "⭐️ Вторая часть (сложные задачи)",
}


def get_user_link(username: Optional[str], user_id: int) -> str:
    """Возвращает ссылку на профиль/диалог в MAX."""
    if username:
        return f"https://max.ru/{username}"
    return f"https://max.ru/id{user_id}"


def get_user_mention(first_name: str, username: Optional[str], user_id: int) -> str:
    """Формирует понятное отображение контакта."""
    if username:
        return f"{first_name} (@{username})"
    return f"{first_name} (ID: {user_id})"


class MaxBotClient:
    """Асинхронный HTTP-клиент для MAX Bot API (platform-api2.max.ru)."""

    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
        }
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_me(self) -> Dict[str, Any]:
        """Получение информации о текущем боте."""
        session = await self.get_session()
        url = f"{MAX_API_BASE}/me"
        async with session.get(url, headers=self.headers) as resp:
            if resp.status == 200:
                return await resp.json()
            err_text = await resp.text()
            raise RuntimeError(f"Ошибка get_me ({resp.status}): {err_text}")

    async def get_updates(self, marker: Optional[int] = None, timeout: int = 25) -> Dict[str, Any]:
        """Long Polling для получения событий."""
        session = await self.get_session()
        params: Dict[str, Any] = {"timeout": timeout}
        if marker is not None:
            params["marker"] = marker
        url = f"{MAX_API_BASE}/updates"
        async with session.get(url, headers=self.headers, params=params) as resp:
            if resp.status == 200:
                return await resp.json()
            err_text = await resp.text()
            logger.warning(f"Ошибка get_updates ({resp.status}): {err_text}")
            return {"updates": [], "marker": marker}

    async def send_message(
        self,
        user_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        text: str = "",
        buttons: Optional[List[List[Dict[str, Any]]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Отправка сообщения пользователю или в чат с поддержкой inline-кнопок."""
        session = await self.get_session()
        url = f"{MAX_API_BASE}/messages"
        params: Dict[str, Any] = {}
        if user_id:
            params["user_id"] = user_id
        elif chat_id:
            params["chat_id"] = chat_id
        else:
            raise ValueError("Необходимо указать user_id или chat_id")

        body: Dict[str, Any] = {"text": text}
        if buttons:
            body["attachments"] = [
                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": buttons
                    }
                }
            ]

        try:
            async with session.post(url, headers=self.headers, params=params, json=body) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                err_text = await resp.text()
                logger.warning(f"Ошибка send_message ({resp.status}) to {user_id or chat_id}: {err_text}")
                return None
        except Exception as e:
            logger.error(f"Исключение при send_message: {e}")
            return None

    async def answer_callback(
        self,
        callback_id: str,
        notification: Optional[str] = None,
        text: Optional[str] = None,
        buttons: Optional[List[List[Dict[str, Any]]]] = None,
    ) -> bool:
        """Ответ на callback нажатия инлайн-кнопки."""
        session = await self.get_session()
        url = f"{MAX_API_BASE}/answers"
        params = {"callback_id": callback_id}

        body: Dict[str, Any] = {}
        if notification:
            body["notification"] = notification

        if text is not None:
            msg_payload: Dict[str, Any] = {"text": text}
            if buttons is not None:
                msg_payload["attachments"] = [
                    {
                        "type": "inline_keyboard",
                        "payload": {
                            "buttons": buttons
                        }
                    }
                ]
            body["message"] = msg_payload
        elif "notification" not in body:
            body["notification"] = ""

        try:
            async with session.post(url, headers=self.headers, params=params, json=body) as resp:
                if resp.status in (200, 201):
                    return True
                err_text = await resp.text()
                logger.warning(f"Ошибка answer_callback ({resp.status}): {err_text}")
                return False
        except Exception as e:
            logger.error(f"Исключение при answer_callback: {e}")
            return False


# In-memory хранилища
user_fsm: Dict[int, Dict[str, Any]] = {}
task_telemost_links: Dict[int, str] = {}


def btn_callback(text: str, payload: str) -> Dict[str, Any]:
    return {"type": "callback", "text": text, "payload": payload}


def btn_link(text: str, url: str) -> Dict[str, Any]:
    return {"type": "link", "text": text, "url": url}


def btn_open_app(text: str, web_app: str = "t334_hakaton_max_bot") -> Dict[str, Any]:
    """Кнопка для открытия Mini App прямо внутри мессенджера МАКС без перехода в браузер."""
    return {"type": "open_app", "text": text, "web_app": web_app, "contact_id": 398783926}


FRONTEND_URL = os.getenv("FRONTEND_URL", "https://135.106.229.213.sslip.io").replace("localhost", "127.0.0.1")


def get_mini_app_url(
    role: Optional[str] = None,
    user_id: Optional[int] = None,
    first_name: Optional[str] = None,
    username: Optional[str] = None,
) -> str:
    """Формирует URL запуска MAX Mini App с передачей данных пользователя."""
    params = []
    if user_id:
        params.append(f"user_id={user_id}")
    if first_name:
        params.append(f"first_name={first_name}")
    if username:
        params.append(f"username={username}")
    if role:
        app_role = "teacher" if role == UserRole.TUTOR.value else "student"
        params.append(f"role={app_role}")
    query = "&".join(params)
    return f"{FRONTEND_URL}/?{query}" if query else FRONTEND_URL


def get_main_menu_buttons(role: str, user: Optional[Any] = None) -> List[List[Dict[str, Any]]]:
    """Главная навигационная клавиатура с нативной кнопкой образовательной платформы."""
    mini_app_btn = [
        btn_open_app("🚀 Открыть образовательную платформу", "t334_hakaton_max_bot"),
    ]

    if role == UserRole.STUDENT.value:
        return [
            mini_app_btn,
            [btn_callback("➕ Сформировать заявку на разбор", "menu:create_task")],
            [btn_callback("📚 Открытый банк заданий ОГЭ", "bank:open_menu")],
            [btn_callback("📂 Реестр моих заявок", "menu:my_tasks"), btn_callback("📹 Яндекс Телемост", "menu:telemost")],
            [btn_callback("👤 Профиль и квалификация", "menu:profile"), btn_callback("👨‍🏫 Кабинет преподавателя", "menu:switch_role")],
            [btn_callback("ℹ️ Регламент платформы", "menu:info")],
        ]
    else:
        return [
            mini_app_btn,
            [btn_callback("📋 Реестр входящих заявок", "menu:tutor_board")],
            [btn_callback("🔒 Закрытый банк (Формирование ДЗ)", "bank:closed_menu")],
            [btn_callback("💼 Заявки в моей работе", "menu:tutor_sessions"), btn_callback("📹 Яндекс Телемост", "menu:telemost")],
            [btn_callback("👤 Профиль и квалификация", "menu:profile"), btn_callback("🎓 Кабинет обучающегося", "menu:switch_role")],
            [btn_callback("ℹ️ Регламент платформы", "menu:info")],
        ]


async def register_or_get_user(sender: Dict[str, Any]) -> User:
    """Регистрация или обновление данных пользователя из MAX в БД."""
    user_id = sender.get("user_id")
    name = sender.get("name") or sender.get("first_name") or "Пользователь MAX"

    # Автоматически парсим юзернейм из всех возможных полей API MAX
    raw_username = sender.get("username") or sender.get("nick") or sender.get("nickname") or sender.get("login")
    username = raw_username.lstrip("@").strip() if raw_username else None

    # Парсим фото / аватар пользователя из MAX
    avatar_url = sender.get("avatar_url") or sender.get("full_avatar_url") or sender.get("photo_url") or sender.get("avatar")

    parts = name.split(maxsplit=1)
    first_name = parts[0] if parts else "Пользователь"
    last_name = parts[1] if len(parts) > 1 else None

    async with AsyncSessionLocal() as session:
        user_in = UserCreate(
            telegram_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url,
        )
        user, created = await crud_user.get_or_create(session, user_in)
        # Если в МАКС задан тег, имя или аватар, ВСЕГДА синхронизируем их в базе автоматически!
        updated = False
        if username and user.username != username:
            user.username = username
            updated = True
        if first_name and user.first_name != first_name and first_name != "Пользователь":
            user.first_name = first_name
            updated = True
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
            updated = True
        if created or updated:
            await session.commit()
            await session.refresh(user)
        return user


async def handle_start_command(client: MaxBotClient, user_id: int, sender: Dict[str, Any]):
    """Обработка команды /start или открытия бота."""
    user = await register_or_get_user(sender)
    role_name = "🎓 Обучающийся (Ученик)" if user.active_role == UserRole.STUDENT.value else "👨‍🏫 Преподаватель (Наставник)"
    title_info = get_user_title(user.active_role, user.xp)

    full_user_name = f"{user.first_name} {user.last_name or ''}".strip()

    text = (
        f"Здравствуйте, {full_user_name}!\n\n"
        f"Добро пожаловать в единую образовательную платформу подготовки к ОГЭ по физике (7–9 классы).\n\n"
        f"Ваш квалификационный статус:\n"
        f"• Рабочий профиль: {role_name}\n"
        f"• Квалификационная категория: {title_info['full_title']}\n"
        f"• Накопленный рейтинг: {user.xp} XP\n\n"
        f"📋 Порядок взаимодействия на платформе:\n"
        f"1. Обучающийся формирует заявку на разбор задания или видеоконсультацию.\n"
        f"2. Преподаватель принимает обращение в работу в Кабинете наставника.\n"
        f"3. Платформа предоставляет прямую связь и персональную видеокомнату в Яндекс Телемосте.\n"
        f"4. По итогам успешного разбора начисляются баллы рейтинга (+100 XP наставнику, +50 XP обучающемуся)."
    )
    buttons = get_main_menu_buttons(user.active_role, user=user)
    await client.send_message(user_id=user_id, text=text, buttons=buttons)


async def handle_profile_view(client: MaxBotClient, user_id: int):
    """Отображение профиля пользователя, баллов, ранга/звания."""
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, user_id)
    if not user:
        user = await register_or_get_user({"user_id": user_id, "name": "Пользователь"})

    title_info = get_user_title(user.active_role, user.xp)
    role_str = "👨‍🏫 Преподаватель" if user.active_role == UserRole.TUTOR.value else "👨‍🎓 Ученик"

    next_goal = ""
    if title_info.get("next_title"):
        next_goal = f"🎯 До следующего звания «{title_info['next_title']}»: осталось {title_info['xp_to_next']} XP\n\n"
    else:
        next_goal = "🏆 Вы достигли высшего звания на платформе!\n\n"

    text = (
        f"👤 Личный профиль ({role_str}):\n\n"
        f"• Имя: {user.first_name} {user.last_name or ''}\n"
        f"• Накоплено очков: {user.xp} XP\n"
        f"• Текущее звание: {title_info['full_title']}\n\n"
        f"{next_goal}"
        f"💡 Начисление очков:\n"
        f"• +100 XP преподавателю за каждую решенную задачу\n"
        f"• +50 XP ученику за закрытие вопроса"
    )
    buttons = [
        [btn_callback("🏠 Главное меню", "menu:main")],
    ]
    await client.send_message(user_id=user_id, text=text, buttons=buttons)


# ==========================================================
# ВКЛАДКА: ЯНДЕКС ТЕЛЕМОСТ
# ==========================================================

async def handle_telemost_tab(client: MaxBotClient, user_id: int):
    """Отдельная вкладка «Яндекс Телемост» со всеми активными созвонами."""
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, user_id)
        if not user:
            return

        # Ищем задачи пользователя в статусе IN_PROGRESS
        if user.active_role == UserRole.TUTOR.value:
            tasks = await crud_task.get_tutor_tasks(session, tutor_id=user.id, status=TaskStatus.IN_PROGRESS.value)
        else:
            tasks = await crud_task.get_student_tasks(session, student_id=user.id, status=TaskStatus.IN_PROGRESS.value)

    if not tasks:
        text = (
            "📹 Вкладка «Яндекс Телемост»\n\n"
            "Здесь автоматически появляются видеозвонки по вашим задачам, находящимся в работе.\n\n"
            "В данный момент у вас нет активных задач со статусом «В работе».\n\n"
            "Вы можете открыть сервис Яндекс Телемост напрямую кнопкой ниже:"
        )
        buttons = [
            [btn_link("🌐 Открыть Яндекс Телемост", "https://telemost.yandex.ru/")],
            [btn_callback("🔙 Главное меню", "menu:main")],
        ]
        await client.send_message(user_id=user_id, text=text, buttons=buttons)
        return

    await client.send_message(
        user_id=user_id,
        text=f"📹 Активные видеовстречи в Яндекс Телемосте (задач в работе: {len(tasks)}):"
    )

    for t in tasks[:3]:
        partner_name = t.student.first_name if user.active_role == UserRole.TUTOR.value else (t.tutor.first_name if t.tutor else "Преподаватель")
        partner_tag = f"@{t.student.username}" if user.active_role == UserRole.TUTOR.value and t.student.username else (f"@{t.tutor.username}" if t.tutor and t.tutor.username else "")

        link = task_telemost_links.get(t.id) or (t.telemost_url if t.telemost_url and "jit.si" not in t.telemost_url else None)
        if link:
            card_text = (
                f"📌 Задача #{t.id} ({t.topic.title if t.topic else 'Физика'})\n"
                f"• Собеседник: {partner_name} {partner_tag}\n"
                f"• Статус звонка: 🟢 Ссылка готова к подключению!"
            )
            buttons = [
                [btn_link("🚀 Подключиться к видеозвонку", link)],
                [btn_callback("🔄 Обновить ссылку Телемоста", f"telemost_new:{t.id}")],
                [btn_callback("🏠 Главное меню", "menu:main")],
            ]
        else:
            card_text = (
                f"📌 Задача #{t.id} ({t.topic.title if t.topic else 'Физика'})\n"
                f"• Собеседник: {partner_name} {partner_tag}\n"
                f"• Статус звонка: ⚪️ Ссылка еще не создана."
            )
            buttons = [
                [btn_callback("📹 Создать звонок в Телемосте", f"telemost:{t.id}")],
                [btn_callback("🏠 Главное меню", "menu:main")],
            ]
        await client.send_message(user_id=user_id, text=card_text, buttons=buttons)


# ==========================================================
# КАБИНЕТ ПРЕПОДАВАТЕЛЯ И ЗАДАЧИ
# ==========================================================

async def handle_show_tutor_board(client: MaxBotClient, user_id: int):
    """Кабинет преподавателя: просмотр свободных задач со статусом OPEN."""
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, user_id)
        if not user:
            return

        if user.active_role != UserRole.TUTOR.value:
            await crud_user.update_active_role(session, user, UserRole.TUTOR.value)
            await session.commit()

        open_tasks = await crud_task.get_board_tasks(session, status=TaskStatus.OPEN.value)

    if not open_tasks:
        text = (
            "📋 Кабинет преподавателя: Свежие задачи\n\n"
            "✨ В данный момент нет открытых задач, ожидающих разбора.\n"
            "Как только ученик опубликует новую заявку, она сразу появится здесь!"
        )
        buttons = [
            [btn_callback("🔄 Обновить список", "menu:tutor_board")],
            [btn_callback("🏠 Главное меню", "menu:main")],
        ]
        await client.send_message(user_id=user_id, text=text, buttons=buttons)
        return

    await client.send_message(
        user_id=user_id,
        text=f"📋 Кабинет преподавателя: Доступные задачи ({len(open_tasks)} шт.):\n\n"
             f"Нажмите «Взять задачу», чтобы запустить разбор и созвон:"
    )

    for task in open_tasks[:5]:
        topic_title = task.topic.title if task.topic else "Физика"
        author_name = task.student.first_name if task.student else "Ученик"
        author_tag = f"@{task.student.username}" if (task.student and task.student.username) else "тег не указан"

        created_str = task.created_at.strftime("%d.%m в %H:%M") if task.created_at else "недавно"
        card_text = (
            f"📌 Заявка #{task.id}\n"
            f"• Раздел/Тема: {topic_title}\n"
            f"• Ученик: {author_name} ({author_tag})\n"
            f"• Вопрос: {task.question}\n"
            f"• Создано: {created_str}\n"
            f"• Желаемое время: {task.scheduled_time}\n"
            f"• Награда: +100 XP и повышение звания"
        )
        buttons = [
            [btn_callback("🤝 Взять задачу", f"accept:{task.id}")],
            [btn_callback("🏠 Главное меню", "menu:main")],
        ]
        await client.send_message(user_id=user_id, text=card_text, buttons=buttons)


async def handle_show_tutor_sessions(client: MaxBotClient, user_id: int):
    """Просмотр разборов преподавателя с понятным @тегом ученика и ссылкой на Телемост."""
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, user_id)
        if not user:
            return
        tasks = await crud_task.get_tutor_tasks(session, tutor_id=user.id)

    if not tasks:
        text = "💼 У вас пока нет взятых задач. Откройте «📋 Свежие задачи (Кабинет)»!"
        buttons = [
            [btn_callback("📋 Свежие задачи", "menu:tutor_board")],
            [btn_callback("🏠 Главное меню", "menu:main")],
        ]
        await client.send_message(user_id=user_id, text=text, buttons=buttons)
        return

    await client.send_message(user_id=user_id, text=f"💼 Ваши разборы в работе (всего {len(tasks)}):")

    for t in tasks[:5]:
        st = "🔵 В работе" if t.status == TaskStatus.IN_PROGRESS.value else "🟢 Завершено"
        s_name = t.student.first_name if t.student else "Ученик"

        telemost_link = task_telemost_links.get(t.id) or (t.telemost_url if t.telemost_url and "jit.si" not in t.telemost_url else None)
        telemost_status = "\n• Видеозвонок: создан" if telemost_link else ""

        created_str = t.created_at.strftime("%d.%m в %H:%M") if t.created_at else "недавно"
        desc = (
            f"📌 Задача #{t.id} — {st}\n"
            f"• Ученик: {s_name}\n"
            f"• Тема: {t.topic.title if t.topic else 'Физика'}\n"
            f"• Вопрос: {t.question}\n"
            f"• Создано: {created_str}\n"
            f"• Время: {t.scheduled_time}{telemost_status}\n\n"
            f"👇 Выберите действие для связи с учеником:"
        )
        buttons = [
            [btn_callback(f"💬 Войти в прямой чат с {s_name}", f"chat_msg:{t.id}")],
            [btn_callback("📹 Видеозвонок (Телемост)", f"telemost:{t.id}")],
            [btn_callback("🏠 Главное меню", "menu:main")],
        ]

        await client.send_message(user_id=user_id, text=desc, buttons=buttons)


async def handle_show_my_tasks(client: MaxBotClient, user_id: int):
    """Просмотр задач ученика с кнопками видеозвонка, контактов и «Вопрос решен»."""
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, user_id)
        if not user:
            user = await register_or_get_user({"user_id": user_id, "name": "Пользователь"})
        tasks = await crud_task.get_student_tasks(session, student_id=user.id)

    if not tasks:
        text = "📂 У вас пока нет созданных заявок. Нажмите «➕ Оставить заявку на разбор»!"
        buttons = [
            [btn_callback("➕ Оставить заявку на разбор", "menu:create_task")],
            [btn_callback("🏠 Главное меню", "menu:main")],
        ]
        await client.send_message(user_id=user_id, text=text, buttons=buttons)
        return

    status_ru = {
        "OPEN": "🟡 Поиск преподавателя",
        "IN_PROGRESS": "🔵 В работе (видеосвязь и чат)",
        "COMPLETED": "🟢 Вопрос решен (+100 XP преподавателю)",
    }

    await client.send_message(user_id=user_id, text=f"📂 Ваши заявки (всего {len(tasks)}):")

    for t in tasks[:5]:
        st = status_ru.get(t.status, t.status)
        t_title = t.topic.title if t.topic else "Тема"
        tutor_info = ""
        tutor_name = ""
        if t.tutor:
            tutor_name = t.tutor.first_name
            tutor_info = f"\n• Преподаватель: {tutor_name}"

        created_str = t.created_at.strftime("%d.%m в %H:%M") if t.created_at else "недавно"
        task_desc = (
            f"📌 Заявка #{t.id} — {st}\n"
            f"• Тема: {t_title}\n"
            f"• Вопрос: {t.question}\n"
            f"• Создано: {created_str}\n"
            f"• Время: {t.scheduled_time}{tutor_info}"
        )

        buttons: List[List[Dict[str, Any]]] = []
        if t.status == TaskStatus.IN_PROGRESS.value and t.tutor:
            buttons.append([btn_callback(f"💬 Войти в прямой чат с {tutor_name}", f"chat_msg:{t.id}")])
            buttons.append([btn_callback("📹 Видеозвонок (Телемост)", f"telemost:{t.id}")])
            buttons.append([btn_callback("✅ Вопрос решен", f"solved:{t.id}")])
        elif t.status == TaskStatus.COMPLETED.value:
            buttons.append([btn_callback("✅ Завершено", f"info_done:{t.id}")])

        buttons.append([btn_callback("🏠 Главное меню", "menu:main")])
        await client.send_message(user_id=user_id, text=task_desc, buttons=buttons)


# ==========================================================
# ВЗАИМНЫЙ ОБМЕН КОНТАКТАМИ («ВЗЯТЬ ЗАДАЧУ»)
# ==========================================================

async def handle_accept_task(client: MaxBotClient, callback_id: str, task_id: int, tutor_user_data: Dict[str, Any]):
    """Преподаватель нажимает «Взять задачу»."""
    tutor_max_id = tutor_user_data.get("user_id")

    async with AsyncSessionLocal() as session:
        tutor = await crud_user.get_by_telegram_id(session, tutor_max_id)
        if not tutor:
            tutor = await register_or_get_user(tutor_user_data)

        task = await crud_task.get_by_id(session, task_id)
        if not task:
            await client.answer_callback(callback_id, notification="Задача не найдена или удалена!")
            return

        if task.status != TaskStatus.OPEN.value:
            await client.answer_callback(callback_id, notification="Эту задачу уже взял другой преподаватель!")
            return

        if task.student_id == tutor.id:
            await client.answer_callback(callback_id, notification="Вы не можете взять свою собственную задачу!")
            return

        await crud_task.accept_task(session, task, tutor_id=tutor.id)
        await session.commit()
        await session.refresh(task)

        student = task.student
        topic_title = task.topic.title if task.topic else "Физика"

    # Меняем кнопку под карточкой задачи на «В работе»
    updated_buttons = [
        [btn_callback("⏳ В работе", f"in_progress:{task_id}")],
    ]
    await client.answer_callback(
        callback_id=callback_id,
        notification="Вы взяли задачу в работу!",
        text=f"📌 Задача #{task_id} взята в работу преподавателем {tutor.first_name}!\n\n🔵 Статус: В работе",
        buttons=updated_buttons,
    )

    student_name = student.first_name
    tutor_name = tutor.first_name

    # 1. Отправляем преподавателю карточку задачи и кнопки связи
    tutor_msg = (
        f"🤝 Вы взяли задачу #{task_id} в работу!\n\n"
        f"👤 Ученик: {student_name}\n"
        f"📚 Тема: {topic_title}\n"
        f"❓ Вопрос: {task.question}\n"
        f"⏰ Время созвона/разбора: {task.scheduled_time}\n\n"
        f"👇 Выберите способ связи с учеником:"
    )
    tutor_buttons: List[List[Dict[str, Any]]] = [
        [btn_callback(f"💬 Войти в прямой чат с {student_name}", f"chat_msg:{task_id}")],
        [btn_callback("📹 Создать звонок в Телемосте", f"telemost:{task_id}")],
        [btn_callback("💼 Мои задачи в работе", "menu:tutor_sessions")],
        [btn_callback("🏠 Главное меню", "menu:main")],
    ]

    await client.send_message(user_id=tutor_max_id, text=tutor_msg, buttons=tutor_buttons)

    # 2. Отправляем ученику уведомление и кнопку связи
    student_msg = (
        f"⚡️ Отличные новости! Преподаватель {tutor_name} взял вашу заявку #{task_id}!\n\n"
        f"👨‍🏫 Преподаватель: {tutor_name}\n"
        f"⏰ Назначенное время: {task.scheduled_time}\n\n"
        f"Преподаватель скоро свяжется с вами или запустит видеозвонок в Телемосте.\n\n"
        f"👇 Вы можете общаться в прямом чате или созвониться в видеовстрече.\n"
        f"После завершения разбора или проверки ДЗ нажмите «Вопрос решен»:"
    )
    student_buttons: List[List[Dict[str, Any]]] = [
        [btn_callback(f"💬 Войти в прямой чат с {tutor_name}", f"chat_msg:{task_id}")],
        [btn_callback("📹 Войти в видеозвонок (Телемост)", f"telemost:{task_id}")],
        [btn_callback("✅ Вопрос решен", f"solved:{task_id}")],
        [btn_callback("🏠 Главное меню", "menu:main")],
    ]

    await client.send_message(user_id=student.telegram_id, text=student_msg, buttons=student_buttons)


# ==========================================================
# ИНТЕГРАЦИЯ ВИДЕОЗВОНКОВ (ЯНДЕКС ТЕЛЕМОСТ)
# ==========================================================

async def handle_telemost_menu(client: MaxBotClient, callback_id: str, user_id: int, task_id: int):
    """Меню видеозвонка: Яндекс Телемост или Быстрая комната."""
    existing_link = task_telemost_links.get(task_id)
    if not existing_link:
        async with AsyncSessionLocal() as session:
            task = await crud_task.get_by_id(session, task_id)
            if task and task.telemost_url and "jit.si" not in task.telemost_url:
                existing_link = task.telemost_url
                task_telemost_links[task_id] = existing_link

    await client.answer_callback(callback_id)

    if existing_link:
        text = (
            f"📹 Видеовстреча по задаче #{task_id} активна!\n\n"
            f"🔗 Ссылка: {existing_link}\n\n"
            f"Нажмите кнопку ниже, чтобы войти в звонок, или создайте новую встречу:"
        )
        buttons = [
            [btn_link("🚀 Подключиться к видеозвонку", existing_link)],
            [btn_callback("🔄 Создать другую ссылку", f"telemost_new:{task_id}")],
            [btn_callback("🔙 В разборы", "menu:tutor_sessions")],
        ]
        await client.send_message(user_id=user_id, text=text, buttons=buttons)
        return

    user_fsm[user_id] = {
        "state": "waiting_telemost_link",
        "data": {"task_id": task_id}
    }

    text = (
        f"📹 Организация видеозвонка в Яндекс Телемосте по задаче #{task_id}\n\n"
        f"1️⃣ Нажмите «🌐 Создать встречу в Телемосте» ниже (в открывшемся окне Яндекса нажмите желтую кнопку «Создать встречу»).\n"
        f"2️⃣ Скопируйте ссылку встречи (вида https://telemost.yandex.ru/j/...) и отправьте сюда в чат.\n\n"
        f"Бот мгновенно перешлет ссылку ученику с кнопкой прямого подключения к звонку!"
    )
    buttons = [
        [btn_link("🌐 Создать встречу в Телемосте", "https://telemost.yandex.ru/")],
        [btn_callback("❌ Отмена", "menu:tutor_sessions")],
    ]
    await client.send_message(user_id=user_id, text=text, buttons=buttons)


async def handle_telemost_quick(client: MaxBotClient, callback_id: str, user_id: int, task_id: int):
    """Мгновенное создание комнаты видеозвонка в 1 клик."""
    await client.answer_callback(callback_id, notification="Видеокомната готова!")

    room_code = 7000000000 + (task_id * 10007) % 2000000000
    room_url = f"https://telemost.yandex.ru/j/{room_code}"
    task_telemost_links[task_id] = room_url

    async with AsyncSessionLocal() as session:
        task = await crud_task.get_by_id(session, task_id)
        if not task:
            return
        task.telemost_url = room_url
        await session.commit()
        student_tg_id = task.student.telegram_id if task.student else None
        tutor_name = task.tutor.first_name if task.tutor else "Преподаватель"

    if student_tg_id:
        student_msg = (
            f"📹 {tutor_name} создал видеокомнату для разбора задачи #{task_id}!\n\n"
            f"Нажмите кнопку ниже, чтобы подключиться к созвону:"
        )
        student_buttons = [
            [btn_link("🚀 Подключиться к видеозвонку", room_url)],
            [btn_callback("✅ Вопрос решен", f"solved:{task_id}")],
        ]
        await client.send_message(user_id=student_tg_id, text=student_msg, buttons=student_buttons)

    tutor_msg = (
        f"✅ Видеокомната по задаче #{task_id} готова!\n\n"
        f"Ученик уже получил приглашение с кнопкой прямого входа.\n"
        f"Нажмите кнопку ниже, чтобы войти в звонок:"
    )
    tutor_buttons = [
        [btn_link("🚀 Войти в видеозвонок", room_url)],
        [btn_callback("💼 Мои задачи в работе", "menu:tutor_sessions")],
    ]
    await client.send_message(user_id=user_id, text=tutor_msg, buttons=tutor_buttons)


async def handle_telemost_link_input(client: MaxBotClient, user_id: int, text_content: str, sender: Dict[str, Any]) -> bool:
    """Обработка ссылки на Яндекс Телемост, вставленной пользователем."""
    if user_id not in user_fsm or user_fsm[user_id].get("state") != "waiting_telemost_link":
        return False

    task_id = user_fsm[user_id]["data"]["task_id"]
    telemost_link = text_content.strip()

    if not (telemost_link.startswith("http://") or telemost_link.startswith("https://") or "telemost" in telemost_link):
        await client.send_message(
            user_id=user_id,
            text="⚠️ Пожалуйста, отправьте ссылку на видеовстречу (например: https://telemost.yandex.ru/j/...).",
            buttons=[
                [btn_link("🌐 Открыть Яндекс Телемост", "https://telemost.yandex.ru/")],
                [btn_callback("❌ Отмена", "menu:tutor_sessions")],
            ]
        )
        return True

    del user_fsm[user_id]
    task_telemost_links[task_id] = telemost_link

    async with AsyncSessionLocal() as session:
        task = await crud_task.get_by_id(session, task_id)
        if not task:
            return True
        task.telemost_url = telemost_link
        await session.commit()
        student_tg_id = task.student.telegram_id if task.student else None
        tutor_name = task.tutor.first_name if task.tutor else "Преподаватель"

    if student_tg_id:
        student_msg = (
            f"📹 {tutor_name} приглашает вас на видеоразбор в Яндекс Телемосте по задаче #{task_id}!\n\n"
            f"Прямая ссылка: {telemost_link}\n\n"
            f"Нажмите кнопку ниже для подключения:"
        )
        student_buttons = [
            [btn_link("🚀 Войти в Яндекс Телемост", telemost_link)],
            [btn_callback("✅ Вопрос решен", f"solved:{task_id}")],
        ]
        await client.send_message(user_id=student_tg_id, text=student_msg, buttons=student_buttons)

    tutor_msg = (
        f"✅ Ссылка на Яндекс Телемост успешно отправлена ученику!\n\n"
        f"Ссылка: {telemost_link}\n\n"
        f"Ожидайте подключения ученика."
    )
    tutor_buttons = [
        [btn_link("🚀 Войти в свой Телемост", telemost_link)],
        [btn_callback("💼 Мои задачи в работе", "menu:tutor_sessions")],
    ]
    await client.send_message(user_id=user_id, text=tutor_msg, buttons=tutor_buttons)
    return True


# ==========================================================
# НЕПРЕРЫВНЫЙ ДИАЛОГ (РЕЖИМ ПРЯМОГО ЧАТА) ЧЕРЕЗ БОТА
# ==========================================================

async def handle_start_chat_msg(client: MaxBotClient, callback_id: str, user_id: int, task_id: int):
    """Вход в режим непрерывного прямого чата по задаче."""
    async with AsyncSessionLocal() as session:
        task = await crud_task.get_by_id(session, task_id)
        if not task:
            await client.answer_callback(callback_id, notification="Задача не найдена.")
            return

        sender_user = await crud_user.get_by_telegram_id(session, user_id)
        if not sender_user:
            await client.answer_callback(callback_id, notification="Пользователь не найден.")
            return

        is_student = (sender_user.id == task.student_id)
        if is_student:
            partner = task.tutor
            partner_name = partner.first_name if partner else "Преподаватель"
            buttons = [
                [btn_callback("📹 Яндекс Телемост", f"telemost:{task.id}")],
                [btn_callback("✅ Вопрос решен", f"solved:{task.id}")],
                [btn_callback("🚪 Выйти в меню", f"chat_exit:{task.id}")],
            ]
        else:
            partner = task.student
            partner_name = partner.first_name if partner else "Ученик"
            buttons = [
                [btn_callback("📹 Яндекс Телемост", f"telemost:{task.id}")],
                [btn_callback("🚪 Выйти в меню", f"chat_exit:{task.id}")],
            ]

    # Переводим пользователя в режим непрерывного чата
    user_fsm[user_id] = {
        "state": "active_chat_session",
        "data": {"task_id": task_id}
    }

    # Переводим собеседника тоже в режим чата, чтобы его ответы шли напрямую
    if partner and partner.telegram_id:
        user_fsm[partner.telegram_id] = {
            "state": "active_chat_session",
            "data": {"task_id": task_id}
        }

    await client.answer_callback(callback_id, notification="Прямой чат открыт!")
    await client.send_message(
        user_id=user_id,
        text=(
            f"🟢 **Прямой диалог открыт с {partner_name} (Заявка #{task_id})**\n\n"
            f"💬 Теперь просто пишите любые сообщения прямо в чат — бот мгновенно пересылает их собеседнику.\n"
            f"Вам больше не нужно каждый раз нажимать кнопки или возвращаться в меню! Общайтесь непрерывно, как в обычной личке.\n\n"
            f"Для завершения диалога или видеосвязи используйте кнопки ниже:"
        ),
        buttons=buttons,
    )


async def handle_relay_text(client: MaxBotClient, user_id: int, text_content: str, sender: Dict[str, Any]) -> bool:
    """Непрерывная пересылка сообщений между участниками диалога без сброса в меню."""
    if user_id not in user_fsm or user_fsm[user_id].get("state") not in ("active_chat_session", "relay_message"):
        return False

    task_id = user_fsm[user_id]["data"]["task_id"]

    # Проверка на выход из режима чата текстовой командой
    cmd = text_content.strip().lower()
    if cmd in ("/exit", "выход", "/menu", "меню", "/stop", "стоп", "/главная", "главная"):
        user_fsm.pop(user_id, None)
        await client.send_message(
            user_id=user_id,
            text="🚪 Вы вышли из режима прямого диалога.",
        )
        await handle_start_command(client, user_id, sender)
        return True

    async with AsyncSessionLocal() as session:
        task = await crud_task.get_by_id(session, task_id)
        if not task or not task.student or not task.tutor:
            user_fsm.pop(user_id, None)
            await client.send_message(user_id=user_id, text="⚠️ Ошибка: участники задачи не найдены.")
            return True

        sender_user = await crud_user.get_by_telegram_id(session, user_id)
        if not sender_user:
            return True

        if sender_user.id == task.tutor_id:
            sender_role = "👨‍🏫 Преподаватель"
            partner_name = task.student.first_name
            recipient_id = task.student.telegram_id
            recipient_buttons = [
                [btn_callback("📹 Яндекс Телемост", f"telemost:{task.id}")],
                [btn_callback("✅ Вопрос решен", f"solved:{task.id}")],
                [btn_callback("🚪 Выйти в меню", f"chat_exit:{task.id}")],
            ]
            sender_buttons = [
                [btn_callback("📹 Яндекс Телемост", f"telemost:{task.id}")],
                [btn_callback("🚪 Выйти в меню", f"chat_exit:{task.id}")],
            ]
        elif sender_user.id == task.student_id:
            sender_role = "👨‍🎓 Ученик"
            partner_name = task.tutor.first_name
            recipient_id = task.tutor.telegram_id
            recipient_buttons = [
                [btn_callback("📹 Яндекс Телемост", f"telemost:{task.id}")],
                [btn_callback("🚪 Выйти в меню", f"chat_exit:{task.id}")],
            ]
            sender_buttons = [
                [btn_callback("📹 Яндекс Телемост", f"telemost:{task.id}")],
                [btn_callback("✅ Вопрос решен", f"solved:{task.id}")],
                [btn_callback("🚪 Выйти в меню", f"chat_exit:{task.id}")],
            ]
        else:
            user_fsm.pop(user_id, None)
            await client.send_message(user_id=user_id, text="Вы не являетесь участником этой задачи.")
            return True

    # Гарантируем, что собеседник тоже находится в режиме непрерывного чата
    user_fsm[recipient_id] = {
        "state": "active_chat_session",
        "data": {"task_id": task_id}
    }

    # 1. Доставляем сообщение собеседнику
    msg_to_recipient = f"{sender_role} {sender_user.first_name}:\n{text_content}"
    await client.send_message(user_id=recipient_id, text=msg_to_recipient, buttons=recipient_buttons)

    # 2. Мягкое подтверждение отправителю с сохранением кнопок (НЕ удаляем user_fsm!)
    msg_ack = f"✓ Доставлено ({partner_name})"
    await client.send_message(user_id=user_id, text=msg_ack, buttons=sender_buttons)

    return True


# ==========================================================
# ЗАВЕРШЕНИЕ РАЗБОРА («ВОПРОС РЕШЕН») И НАЧИСЛЕНИЕ ОЧКОВ
# ==========================================================

async def handle_solve_task(client: MaxBotClient, callback_id: str, task_id: int, student_user_data: Dict[str, Any]):
    """Ученик подтверждает завершение задачи кнопкой «Вопрос решен»."""
    student_max_id = student_user_data.get("user_id")

    async with AsyncSessionLocal() as session:
        student = await crud_user.get_by_telegram_id(session, student_max_id)
        task = await crud_task.get_by_id(session, task_id)
        if not task:
            await client.answer_callback(callback_id, notification="Задача не найдена.")
            return

        if task.status == TaskStatus.COMPLETED.value:
            await client.answer_callback(callback_id, notification="Эта задача уже была успешно завершена!")
            return

        if student and task.student_id != student.id:
            await client.answer_callback(callback_id, notification="Только автор заявки может подтвердить решение!")
            return

        task, tutor_xp, _ = await crud_task.complete_task(session, task)
        await session.commit()
        await session.refresh(task)

        tutor = task.tutor
        topic_title = task.topic.title if task.topic else "Физика"

    # Завершаем режим чата для участников этой задачи
    for uid, fsm in list(user_fsm.items()):
        if fsm.get("data", {}).get("task_id") == task_id or fsm.get("task_id") == task_id:
            user_fsm.pop(uid, None)

    await client.answer_callback(
        callback_id=callback_id,
        notification="✅ Вопрос отмечен как решенный!",
        text=f"✅ Задача #{task_id} успешно завершена! Спасибо за помощь.",
        buttons=[[btn_callback("📂 Мои заявки", "menu:my_tasks")]],
    )

    student_title_info = get_user_title("student", student.xp if student else 0)
    student_congrats = (
        f"🎉 Заявка #{task_id} закрыта со статусом «Вопрос решен»!\n\n"
        f"Вам начислено +50 XP за продуктивность. 🌟\n"
        f"• Ваш баланс: {student.xp if student else 0} XP\n"
        f"• Ваше звание: {student_title_info['full_title']}\n\n"
        f"Рады были помочь вам разобраться в физике!"
    )
    await client.send_message(user_id=student_max_id, text=student_congrats)

    if tutor:
        tutor_title_info = get_user_title("tutor", tutor.xp)
        tutor_congrats = (
            f"🏆 Ученик подтвердил: «Вопрос решен» по задаче #{task_id} ({topic_title})!\n\n"
            f"Вам начислено: +100 XP за успешную помощь ученику! 🎯\n"
            f"• Ваш текущий баланс: {tutor.xp} XP\n"
            f"• Ваше звание: {tutor_title_info['full_title']}\n"
        )
        if tutor_title_info.get("next_title"):
            tutor_congrats += f"• До следующего звания ({tutor_title_info['next_title']}): {tutor_title_info['xp_to_next']} XP\n"
        else:
            tutor_congrats += "• Поздравляем! Вы достигли высшего звания на платформе!\n"

        await client.send_message(
            user_id=tutor.telegram_id,
            text=tutor_congrats,
            buttons=[[btn_callback("📋 Свежие задачи", "menu:tutor_board")]],
        )


# ==========================================================
# БАНК ЗАДАЧ: ОТКРЫТЫЙ (ДЛЯ УЧЕНИКОВ) И ЗАКРЫТЫЙ (ДЛЯ ДЗ)
# ==========================================================

async def handle_open_bank_menu(client: MaxBotClient, user_id: int):
    """Выбор класса для тренировки в открытом банке задач."""
    text = (
        "📚 Открытый банк задач по физике (7–9 классы)\n\n"
        "Здесь собраны тренировочные задачи для отработки тем и подготовки к ОГЭ. "
        "Вы можете решать их самостоятельно, вводить ответы для самопроверки и смотреть подробные решения с подсказками!\n\n"
        "Выберите ваш класс:"
    )
    buttons = [
        [btn_callback("7️⃣ 7 класс (Начальная механика)", "bank:open_grade:7")],
        [btn_callback("8️⃣ 8 класс (Теплота, Электричество, Оптика)", "bank:open_grade:8")],
        [btn_callback("9️⃣ 9 класс (Динамика, Кванты, ОГЭ №20-25)", "bank:open_grade:9")],
        [btn_callback("🏠 Главное меню", "menu:main")],
    ]
    await client.send_message(user_id=user_id, text=text, buttons=buttons)


async def handle_open_bank_grade(client: MaxBotClient, callback_id: str, user_id: int, grade: int):
    """Выбор раздела физики для выбранного класса."""
    await client.answer_callback(callback_id)
    async with AsyncSessionLocal() as session:
        blocks = await crud_bank_task.get_available_blocks(session, grade=grade, bank_type=BankType.OPEN.value)

    if not blocks:
        await client.send_message(
            user_id=user_id,
            text=f"В {grade} классе пока нет активных задач в открытом банке.",
            buttons=[[btn_callback("🔙 Назад", "bank:open_menu")]]
        )
        return

    buttons = []
    for b in blocks:
        b_name = BLOCK_NAMES.get(b, b)
        buttons.append([btn_callback(b_name, f"bank:open_block:{grade}:{b}")])
    buttons.append([btn_callback("🔙 Выбрать класс", "bank:open_menu")])

    text = f"📚 {grade} класс — Открытый банк задач\n\nВыберите интересующий раздел физики:"
    await client.send_message(user_id=user_id, text=text, buttons=buttons)


async def handle_open_bank_block(client: MaxBotClient, callback_id: str, user_id: int, grade: int, block: str):
    """Список задач открытого банка по классу и разделу."""
    await client.answer_callback(callback_id)
    async with AsyncSessionLocal() as session:
        tasks = await crud_bank_task.get_tasks(session, grade=grade, block=block, bank_type=BankType.OPEN.value, limit=10)

    if not tasks:
        await client.send_message(
            user_id=user_id,
            text="В этом разделе пока нет задач.",
            buttons=[[btn_callback("🔙 К разделам", f"bank:open_grade:{grade}")]]
        )
        return

    b_name = BLOCK_NAMES.get(block, block)
    text = (
        f"📚 {grade} класс • {b_name}\n\n"
        f"Найдено тренировочных задач: {len(tasks)}\n"
        f"Нажмите на задачу для решения и проверки:"
    )
    buttons = []
    for t in tasks:
        buttons.append([btn_callback(f"• {t.title} ({t.difficulty})", f"bank:open_task:{t.id}")])
    buttons.append([btn_callback("🔙 К разделам", f"bank:open_grade:{grade}")])
    buttons.append([btn_callback("🏠 Главное меню", "menu:main")])

    await client.send_message(user_id=user_id, text=text, buttons=buttons)


async def handle_open_bank_task_view(client: MaxBotClient, callback_id: str, user_id: int, task_id: int):
    """Карточка задачи открытого банка для ученика."""
    await client.answer_callback(callback_id)
    async with AsyncSessionLocal() as session:
        t = await crud_bank_task.get_by_id(session, task_id)

    if not t:
        await client.send_message(user_id=user_id, text="Задача не найдена.")
        return

    text = (
        f"📌 Задача #{t.id}: {t.title}\n"
        f"• Класс: {t.grade} класс | Сложность: {t.difficulty}\n"
        f"• Тема: {t.topic_title}\n\n"
        f"❓ Условие:\n{t.statement}\n\n"
        f"👇 Проверьте себя или воспользуйтесь подсказкой:"
    )
    buttons = [
        [btn_callback("✍️ Проверить свой ответ (+15 XP)", f"bank:ans_prompt:{t.id}")],
        [btn_callback("💡 Подсказка", f"bank:hint:{t.id}"), btn_callback("📖 Показать решение", f"bank:sol:{t.id}")],
        [btn_callback("🔙 К списку задач", f"bank:open_block:{t.grade}:{t.block}")],
        [btn_callback("🏠 Главное меню", "menu:main")],
    ]
    await client.send_message(user_id=user_id, text=text, buttons=buttons)


async def handle_open_bank_hint(client: MaxBotClient, callback_id: str, user_id: int, task_id: int):
    """Вывод подсказки к задаче."""
    async with AsyncSessionLocal() as session:
        t = await crud_bank_task.get_by_id(session, task_id)

    hint_text = t.hint if (t and t.hint) else "Внимательно проанализируйте условие и запишите дано в СИ."
    await client.answer_callback(callback_id, notification="💡 Подсказка открыта!")
    await client.send_message(
        user_id=user_id,
        text=f"💡 Подсказка к задаче #{task_id} ({t.title}):\n\n{hint_text}",
        buttons=[[btn_callback("🔙 Вернуться к задаче", f"bank:open_task:{task_id}")]]
    )


async def handle_open_bank_solution(client: MaxBotClient, callback_id: str, user_id: int, task_id: int):
    """Вывод полного решения задачи."""
    async with AsyncSessionLocal() as session:
        t = await crud_bank_task.get_by_id(session, task_id)

    if not t:
        return
    await client.answer_callback(callback_id, notification="Решение загружено")
    text = (
        f"📖 Полное решение задачи #{t.id}: {t.title}\n\n"
        f"{t.solution}\n\n"
        f"✅ Правильный ответ: {t.answer}"
    )
    await client.send_message(
        user_id=user_id,
        text=text,
        buttons=[[btn_callback("🔙 К задаче", f"bank:open_task:{task_id}")], [btn_callback("🏠 Главное меню", "menu:main")]]
    )


async def handle_open_bank_answer_prompt(client: MaxBotClient, callback_id: str, user_id: int, task_id: int):
    """Запрос ввода ответа у ученика для проверки."""
    user_fsm[user_id] = {
        "state": "checking_bank_answer",
        "data": {"task_id": task_id}
    }
    await client.answer_callback(callback_id)
    await client.send_message(
        user_id=user_id,
        text=(
            f"✍️ Проверка ответа по задаче #{task_id}:\n\n"
            f"Введите полученный вами ответ (число или краткое слово) сообщением в чат.\n\n"
            f"Пример: 2.8 или 50"
        ),
        buttons=[[btn_callback("❌ Отмена", f"bank:open_task:{task_id}")]]
    )


# ==========================================================
# ЗАКРЫТЫЙ БАНК ЗАДАЧ (ДЛЯ ПРЕПОДАВАТЕЛЕЙ / ВЫДАЧА ДЗ)
# ==========================================================

async def handle_closed_bank_menu(client: MaxBotClient, user_id: int):
    """Главное меню закрытого банка задач для преподавателей."""
    async with AsyncSessionLocal() as session:
        total = await crud_bank_task.count_tasks(session, bank_type=BankType.CLOSED.value)

    text = (
        f"🔒 Закрытый банк задач (Банк домашних заданий)\n\n"
        f"🛡️ Защита от списывания:\n"
        f"Задачи из этой базы скрыты от учеников. Их условий и ответов нет в открытом доступе или ГДЗ!\n\n"
        f"Всего доступно авторских задач в закрытом банке: {total}.\n\n"
        f"Вы можете выбрать задачу и в 1 клик выдать её ученику в качестве ДЗ после проведенного урока.\n\n"
        f"Выберите класс:"
    )
    buttons = [
        [btn_callback("7️⃣ 7 класс (Закрытый банк)", "bank:closed_grade:7")],
        [btn_callback("8️⃣ 8 класс (Закрытый банк)", "bank:closed_grade:8")],
        [btn_callback("9️⃣ 9 класс (Закрытый банк ОГЭ)", "bank:closed_grade:9")],
        [btn_callback("🏠 Главное меню", "menu:main")],
    ]
    await client.send_message(user_id=user_id, text=text, buttons=buttons)


async def handle_closed_bank_grade(client: MaxBotClient, callback_id: str, user_id: int, grade: int):
    """Выбор раздела закрытого банка для преподавателя."""
    await client.answer_callback(callback_id)
    async with AsyncSessionLocal() as session:
        blocks = await crud_bank_task.get_available_blocks(session, grade=grade, bank_type=BankType.CLOSED.value)

    if not blocks:
        await client.send_message(
            user_id=user_id,
            text=f"В {grade} классе пока нет задач в закрытом банке.",
            buttons=[[btn_callback("🔙 Назад", "bank:closed_menu")]]
        )
        return

    buttons = []
    for b in blocks:
        b_name = BLOCK_NAMES.get(b, b)
        buttons.append([btn_callback(b_name, f"bank:closed_block:{grade}:{b}")])
    buttons.append([btn_callback("🔙 Выбрать класс", "bank:closed_menu")])

    text = f"🔒 {grade} класс — Закрытый банк (Анти-списывание)\n\nВыберите раздел для подбора ДЗ:"
    await client.send_message(user_id=user_id, text=text, buttons=buttons)


async def handle_closed_bank_block(client: MaxBotClient, callback_id: str, user_id: int, grade: int, block: str):
    """Список задач закрытого банка для преподавателя."""
    await client.answer_callback(callback_id)
    async with AsyncSessionLocal() as session:
        tasks = await crud_bank_task.get_tasks(session, grade=grade, block=block, bank_type=BankType.CLOSED.value, limit=10)

    b_name = BLOCK_NAMES.get(block, block)
    text = (
        f"🔒 {grade} класс • {b_name} (Закрытый банк)\n\n"
        f"Доступно авторских задач для ДЗ: {len(tasks)}\n"
        f"Выберите задачу для просмотра и выдачи ученику:"
    )
    buttons = []
    for t in tasks:
        buttons.append([btn_callback(f"🔒 {t.title} ({t.difficulty})", f"bank:closed_task:{t.id}")])
    buttons.append([btn_callback("🔙 К разделам", f"bank:closed_grade:{grade}")])
    buttons.append([btn_callback("🏠 Главное меню", "menu:main")])

    await client.send_message(user_id=user_id, text=text, buttons=buttons)


async def handle_closed_bank_task_view(client: MaxBotClient, callback_id: str, user_id: int, task_id: int):
    """Просмотр задачи закрытого банка преподавателем (с ответом и решением)."""
    await client.answer_callback(callback_id)
    async with AsyncSessionLocal() as session:
        t = await crud_bank_task.get_by_id(session, task_id)

    if not t:
        return

    text = (
        f"🔒 Задача #{t.id}: {t.title} ({t.grade} класс, {t.difficulty})\n"
        f"Тема: {t.topic_title}\n\n"
        f"❓ Условие для ученика:\n{t.statement}\n\n"
        f"🎯 Эталонный ответ: {t.answer}\n\n"
        f"📝 Критерии и решение (видно только вам):\n{t.solution}\n\n"
        f"👇 Нажмите ниже, чтобы выдать эту задачу ученику:"
    )
    buttons = [
        [btn_callback("📤 Выдать эту задачу как ДЗ ученику", f"bank:assign_pick:{t.id}")],
        [btn_callback("🔙 К списку", f"bank:closed_block:{t.grade}:{t.block}")],
        [btn_callback("🏠 Главное меню", "menu:main")],
    ]
    await client.send_message(user_id=user_id, text=text, buttons=buttons)


async def handle_assign_pick_student(client: MaxBotClient, callback_id: str, user_id: int, bank_task_id: int):
    """Выбор заявки/ученика для выдачи ДЗ."""
    async with AsyncSessionLocal() as session:
        user = await crud_user.get_by_telegram_id(session, user_id)
        if not user:
            return
        tasks = await crud_task.get_tutor_tasks(session, tutor_id=user.id, status=TaskStatus.IN_PROGRESS.value)

    if not tasks:
        await client.answer_callback(callback_id, notification="Нет активных задач в работе!")
        await client.send_message(
            user_id=user_id,
            text=(
                "ℹ️ У вас сейчас нет взятых заявок в статусе «В работе».\n\n"
                "Когда вы возьмете задачу ученика через Кабинет преподавателя, вы сможете в 1 клик прикрепить это ДЗ.\n"
                "Вы также можете скопировать условие задачи прямо сейчас."
            ),
            buttons=[
                [btn_callback("📋 Свежие задачи", "menu:tutor_board")],
                [btn_callback("🔙 Назад к задаче", f"bank:closed_task:{bank_task_id}")],
            ]
        )
        return

    await client.answer_callback(callback_id)
    buttons = []
    for t in tasks:
        s_name = t.student.first_name if t.student else "Ученик"
        buttons.append([btn_callback(f"👤 {s_name} (Заявка #{t.id})", f"bank:assign_exec:{bank_task_id}:{t.id}")])
    buttons.append([btn_callback("❌ Отмена", f"bank:closed_task:{bank_task_id}")])

    await client.send_message(
        user_id=user_id,
        text=f"Выберите ученика, которому нужно назначить ДЗ #{bank_task_id}:",
        buttons=buttons,
    )


async def handle_assign_exec(client: MaxBotClient, callback_id: str, user_id: int, bank_task_id: int, task_id: int):
    """Исполнение назначения задачи из закрытого банка в ДЗ ученику."""
    async with AsyncSessionLocal() as session:
        bank_task = await crud_bank_task.get_by_id(session, bank_task_id)
        task = await crud_task.get_by_id(session, task_id)
        tutor = await crud_user.get_by_telegram_id(session, user_id)

        if not bank_task or not task or not tutor:
            await client.answer_callback(callback_id, notification="Ошибка данных")
            return

        hw_text = (
            f"🔒 Контрольное ДЗ из закрытого банка ({bank_task.grade} класс, {bank_task.difficulty}):\n"
            f"«{bank_task.title}»\n\n"
            f"{bank_task.statement}"
        )
        hw_in = HomeworkCreate(task_text=hw_text)
        hw = await crud_homework.create(
            session=session,
            task=task,
            tutor_id=tutor.id,
            homework_in=hw_in,
        )
        await session.commit()
        await session.refresh(hw)

        student_tg_id = task.student.telegram_id if task.student else None
        student_name = task.student.first_name if task.student else "Ученик"

    await client.answer_callback(callback_id, notification="ДЗ успешно выдано!")
    await client.send_message(
        user_id=user_id,
        text=f"✅ Задача #{bank_task_id} («{bank_task.title}») успешно назначена ученику {student_name} в качестве ДЗ!",
        buttons=[
            [btn_callback(f"💬 Открыть чат с {student_name}", f"chat_msg:{task_id}")],
            [btn_callback("💼 Мои задачи в работе", "menu:tutor_sessions")],
            [btn_callback("🏠 Главное меню", "menu:main")],
        ]
    )

    # Уведомляем ученика
    if student_tg_id:
        student_hw_msg = (
            f"📝 Преподаватель {tutor.first_name} выдал вам контрольное домашнее задание по задаче #{task_id}!\n\n"
            f"🔒 **Задание из закрытого банка:**\n"
            f"**{bank_task.title}** ({bank_task.grade} класс)\n"
            f"Тема: {bank_task.topic_title}\n\n"
            f"❓ **Условие:**\n{bank_task.statement}\n\n"
            f"🛡️ *Обратите внимание: этого задания нет в открытом доступе и ГДЗ.*\n\n"
            f"Решите задачу в тетради или напишите ответ преподавателю в чат!"
        )
        student_buttons = [
            [btn_callback(f"💬 Открыть чат с {tutor.first_name}", f"chat_msg:{task_id}")],
            [btn_callback("✅ Вопрос решен", f"solved:{task_id}")],
        ]
        await client.send_message(user_id=student_tg_id, text=student_hw_msg, buttons=student_buttons)


# ==========================================================
# ПОШАГОВОЕ СОЗДАНИЕ ЗАЯВКИ С ПРОВЕРКОЙ @ТЕГА (FSM)
# ==========================================================

async def handle_start_create_task(client: MaxBotClient, user_id: int):
    """Старт создания заявки на разбор задачи: сразу выбор раздела."""
    await prompt_choose_block(client, user_id)


async def prompt_choose_block(client: MaxBotClient, user_id: int):
    """Шаг 1 из 3: Выбор раздела физики."""
    user_fsm[user_id] = {"state": "choose_block", "data": {}}

    buttons = []
    for code, title in BLOCK_NAMES.items():
        buttons.append([btn_callback(title, f"fsm_block:{code}")])
    buttons.append([btn_callback("❌ Отмена", "menu:main")])

    text = (
        "➕ **Создание заявки на разбор задачи**\n\n"
        "📚 **Шаг 1 из 3: Выберите раздел физики:**"
    )
    await client.send_message(user_id=user_id, text=text, buttons=buttons)


async def handle_fsm_block_chosen(client: MaxBotClient, callback_id: str, user_id: int, block_code: str):
    """Выбор темы из выбранного раздела."""
    if user_id not in user_fsm:
        user_fsm[user_id] = {"state": "choose_topic", "data": {}}
    user_fsm[user_id]["data"]["block"] = block_code

    async with AsyncSessionLocal() as session:
        topics = await crud_topic.get_all(session, block=block_code, is_active=True)

    buttons = []
    for t in topics[:6]:
        short_title = t.title if len(t.title) <= 40 else t.title[:37] + "..."
        buttons.append([btn_callback(f"• {short_title}", f"fsm_topic:{t.id}")])
    buttons.append([btn_callback("🔙 Назад к разделам", "menu:create_task")])

    block_name = BLOCK_NAMES.get(block_code, block_code)
    await client.answer_callback(callback_id)
    await client.send_message(
        user_id=user_id,
        text=f"Раздел «{block_name}».\nВыберите конкретную тему вопроса:",
        buttons=buttons,
    )
    user_fsm[user_id]["state"] = "choose_topic"


async def handle_fsm_topic_chosen(client: MaxBotClient, callback_id: str, user_id: int, topic_id: int):
    """Запрос текста вопроса и времени."""
    if user_id not in user_fsm:
        user_fsm[user_id] = {"state": "enter_question", "data": {}}
    user_fsm[user_id]["data"]["topic_id"] = topic_id
    user_fsm[user_id]["state"] = "enter_question"

    await client.answer_callback(callback_id)
    text = (
        "Опишите суть проблемы:\n\n"
        "Отправьте сообщением в чат:\n"
        "1. В чем конкретно затык или условие задачи?\n"
        "2. В какое время вам удобно созвониться в Телемосте?\n\n"
        "Пример сообщения:\n"
        "«Не понимаю формулу КПД рычага. Удобно сегодня в 19:00»"
    )
    await client.send_message(
        user_id=user_id,
        text=text,
        buttons=[[btn_callback("❌ Отмена", "menu:main")]],
    )


async def handle_fsm_text_input(client: MaxBotClient, user_id: int, text_content: str, sender: Dict[str, Any]):
    """Обработка введенного текста вопроса и сохранение задачи в БД."""
    if user_id not in user_fsm or user_fsm[user_id].get("state") != "enter_question":
        return False

    fsm_data = user_fsm.pop(user_id)["data"]
    topic_id = fsm_data.get("topic_id", 1)

    scheduled_time = "В ближайшее время"
    if "удобно" in text_content.lower() or "сегодня" in text_content.lower() or "завтра" in text_content.lower():
        parts = text_content.split("Удобно", 1)
        if len(parts) > 1:
            scheduled_time = parts[1].strip(" :.!-")
    elif "в " in text_content.lower():
        scheduled_time = "Сегодня"

    user = await register_or_get_user(sender)

    async with AsyncSessionLocal() as session:
        task_in = TaskCreate(
            topic_id=topic_id,
            part=TaskPart.PART_1.value,
            photo_url="uploads/tasks/default_physics.png",
            question=text_content,
            scheduled_time=scheduled_time,
        )
        task = await crud_task.create(session, student_id=user.id, task_in=task_in)
        await session.commit()
        await session.refresh(task)

        topic = await crud_topic.get_by_id(session, topic_id)
        topic_title = topic.title if topic else "Физика"

        tutors_res = await session.execute(
            select(User).where(User.active_role == UserRole.TUTOR.value)
        )
        tutors = list(tutors_res.scalars().all())

    # Сообщение ученику
    student_success = (
        f"🎉 Заявка #{task.id} успешно создана и опубликована в кабинете преподавателей!\n\n"
        f"• Тема: {topic_title}\n"
        f"• Вопрос: {task.question}\n"
        f"• Время: {task.scheduled_time}\n\n"
        f"Как только преподаватель возьмет задачу, бот откроет чат для разбора и создаст видеовстречу в Телемосте!"
    )
    await client.send_message(
        user_id=user_id,
        text=student_success,
        buttons=[
            [btn_callback("📂 Мои заявки", "menu:my_tasks")],
            [btn_callback("🏠 Главное меню", "menu:main")],
        ],
    )

    # Оповещаем зарегистрированных преподавателей
    tutor_broadcast = (
        f"🔔 Новая задача по физике! (Заявка #{task.id})\n\n"
        f"• Тема: {topic_title}\n"
        f"• Ученик: {user.first_name}\n"
        f"• Вопрос: {task.question}\n"
        f"• Время: {task.scheduled_time}\n\n"
        f"Нажмите «Взять задачу», чтобы запустить разбор и созвон:"
    )
    tutor_accept_button = [
        [btn_callback("🤝 Взять задачу", f"accept:{task.id}")],
    ]

    for tutor in tutors:
        if tutor.telegram_id != user_id:
            try:
                await client.send_message(
                    user_id=tutor.telegram_id,
                    text=tutor_broadcast,
                    buttons=tutor_accept_button,
                )
            except Exception as e:
                logger.warning(f"Не удалось отправить уведомление преподавателю {tutor.telegram_id}: {e}")

    return True


# ==========================================================
# ОБРАБОТЧИК КНОПОК И ТЕКСТОВЫХ КОМАНД
# ==========================================================

async def process_callback(client: MaxBotClient, update: Dict[str, Any]):
    """Маршрутизация всех нажатий инлайн-кнопок."""
    callback = update.get("callback", {})
    callback_id = callback.get("callback_id")
    payload = callback.get("payload", "")
    user_data = callback.get("user", {})
    user_id = user_data.get("user_id")

    if not callback_id:
        return

    logger.info(f"Получен callback '{payload}' от user_id={user_id}")

    # Автоматически синхронизируем пользователя и его @тег из МАКС при любом нажатии кнопки
    if user_data and user_id:
        await register_or_get_user(user_data)

    # Взятие задачи преподавателем
    if payload.startswith("accept:"):
        task_id = int(payload.split(":", 1)[1])
        await handle_accept_task(client, callback_id, task_id, user_data)
        return

    # Завершение задачи учеником («Вопрос решен»)
    if payload.startswith("solved:"):
        task_id = int(payload.split(":", 1)[1])
        await handle_solve_task(client, callback_id, task_id, user_data)
        return

    # Видеозвонок (Телемост)
    if payload.startswith("telemost:") or payload.startswith("telemost_new:"):
        task_id = int(payload.split(":", 1)[1])
        if payload.startswith("telemost_new:"):
            task_telemost_links.pop(task_id, None)
            async with AsyncSessionLocal() as session:
                t = await crud_task.get_by_id(session, task_id)
                if t:
                    t.telemost_url = ""
                    await session.commit()
        await handle_telemost_menu(client, callback_id, user_id, task_id)
        return

    # Быстрый видеозвонок в 1 клик
    if payload.startswith("quick_call:"):
        task_id = int(payload.split(":", 1)[1])
        await handle_telemost_quick(client, callback_id, user_id, task_id)
        return

    # Чат через бота
    if payload.startswith("chat_msg:"):
        task_id = int(payload.split(":", 1)[1])
        await handle_start_chat_msg(client, callback_id, user_id, task_id)
        return

    if payload.startswith("chat_exit:"):
        user_fsm.pop(user_id, None)
        await client.answer_callback(callback_id, notification="Вы вышли из режима чата")
        await client.send_message(
            user_id=user_id,
            text="🚪 Вы вышли из режима прямого диалога.",
            buttons=[[btn_callback("🏠 Главное меню", "menu:main")]]
        )
        await handle_start_command(client, user_id, user_data)
        return

    if payload.startswith("in_progress:"):
        task_id = int(payload.split(":", 1)[1])
        await client.answer_callback(callback_id, notification=f"Эта задача #{task_id} уже находится в работе.")
        return

    if payload.startswith("info_done:"):
        await client.answer_callback(callback_id, notification="Задача уже завершена. Очки начислены!")
        return

    # FSM создания задачи
    if payload.startswith("fsm_block:"):
        block_code = payload.split(":", 1)[1]
        await handle_fsm_block_chosen(client, callback_id, user_id, block_code)
        return

    if payload.startswith("fsm_topic:"):
        topic_id = int(payload.split(":", 1)[1])
        await handle_fsm_topic_chosen(client, callback_id, user_id, topic_id)
        return

    # Навигационное меню
    if payload == "menu:main":
        await client.answer_callback(callback_id)
        await handle_start_command(client, user_id, user_data)
        return

    # Роутинг Открытого банка задач
    if payload == "bank:open_menu":
        await client.answer_callback(callback_id)
        await handle_open_bank_menu(client, user_id)
        return

    if payload.startswith("bank:open_grade:"):
        grade = int(payload.split(":", 2)[2])
        await handle_open_bank_grade(client, callback_id, user_id, grade)
        return

    if payload.startswith("bank:open_block:"):
        parts = payload.split(":", 3)
        grade = int(parts[2])
        block = parts[3]
        await handle_open_bank_block(client, callback_id, user_id, grade, block)
        return

    if payload.startswith("bank:open_task:"):
        task_id = int(payload.split(":", 2)[2])
        await handle_open_bank_task_view(client, callback_id, user_id, task_id)
        return

    if payload.startswith("bank:hint:"):
        task_id = int(payload.split(":", 2)[2])
        await handle_open_bank_hint(client, callback_id, user_id, task_id)
        return

    if payload.startswith("bank:sol:"):
        task_id = int(payload.split(":", 2)[2])
        await handle_open_bank_solution(client, callback_id, user_id, task_id)
        return

    if payload.startswith("bank:ans_prompt:"):
        task_id = int(payload.split(":", 2)[2])
        await handle_open_bank_answer_prompt(client, callback_id, user_id, task_id)
        return

    # Роутинг Закрытого банка задач
    if payload == "bank:closed_menu":
        await client.answer_callback(callback_id)
        await handle_closed_bank_menu(client, user_id)
        return

    if payload.startswith("bank:closed_grade:"):
        grade = int(payload.split(":", 2)[2])
        await handle_closed_bank_grade(client, callback_id, user_id, grade)
        return

    if payload.startswith("bank:closed_block:"):
        parts = payload.split(":", 3)
        grade = int(parts[2])
        block = parts[3]
        await handle_closed_bank_block(client, callback_id, user_id, grade, block)
        return

    if payload.startswith("bank:closed_task:"):
        task_id = int(payload.split(":", 2)[2])
        await handle_closed_bank_task_view(client, callback_id, user_id, task_id)
        return

    if payload.startswith("bank:assign_pick:"):
        task_id = int(payload.split(":", 2)[2])
        await handle_assign_pick_student(client, callback_id, user_id, task_id)
        return

    if payload.startswith("bank:assign_exec:"):
        parts = payload.split(":")
        bank_task_id = int(parts[2])
        task_id = int(parts[3])
        await handle_assign_exec(client, callback_id, user_id, bank_task_id, task_id)
        return

    if payload == "menu:telemost":
        await client.answer_callback(callback_id)
        await handle_telemost_tab(client, user_id)
        return

    if payload == "menu:set_tag":
        user_fsm[user_id] = {"state": "setting_tag_manually", "data": {}}
        await client.answer_callback(callback_id)
        await client.send_message(
            user_id=user_id,
            text=(
                "✍️ Введите ваш @тег (никнейм в МАКС, например: `@ivan` или `@polina`):\n\n"
                "Он будет сохранен в вашем профиле и показан собеседникам."
            ),
            buttons=[[btn_callback("❌ Отмена", "menu:profile")]]
        )
        return

    if payload == "menu:create_task":
        await client.answer_callback(callback_id)
        await handle_start_create_task(client, user_id)
        return

    if payload == "menu:tutor_board":
        await client.answer_callback(callback_id)
        await handle_show_tutor_board(client, user_id)
        return

    if payload == "menu:my_tasks":
        await client.answer_callback(callback_id)
        await handle_show_my_tasks(client, user_id)
        return

    if payload == "menu:tutor_sessions":
        await client.answer_callback(callback_id)
        await handle_show_tutor_sessions(client, user_id)
        return

    if payload == "menu:profile":
        await client.answer_callback(callback_id)
        await handle_profile_view(client, user_id)
        return

    if payload == "menu:switch_role":
        async with AsyncSessionLocal() as session:
            user = await crud_user.get_by_telegram_id(session, user_id)
            if not user:
                user = await register_or_get_user(user_data)
            new_role = UserRole.TUTOR.value if user.active_role == UserRole.STUDENT.value else UserRole.STUDENT.value
            await crud_user.update_active_role(session, user, new_role)
            await session.commit()
            role_label = "Кабинет преподавателя 👨‍🏫" if new_role == "tutor" else "Режим ученика 👨‍🎓"

        await client.answer_callback(callback_id, notification=f"Переключено: {role_label}")
        await handle_start_command(client, user_id, user_data)
        return

    if payload == "menu:info":
        info_text = (
            "ℹ️ Как работает сервис взаимопомощи по физике:\n\n"
            "1. Ученик оставляет заявку на разбор темы или задачи.\n"
            "2. Преподаватели видят её в Кабинете преподавателя и жмут «Взять задачу».\n"
            "3. Бот мгновенно передает @теги для связи в личке МАКС и создает видеозвонок в Телемосте!\n"
            "4. Вы созваниваетесь по видеосвязи и разбираете сложную задачу.\n"
            "5. Ученик нажимает «Вопрос решен» — преподавателю зачисляются +100 XP и растет его звание!"
        )
        await client.answer_callback(callback_id)
        await client.send_message(
            user_id=user_id,
            text=info_text,
            buttons=[[btn_callback("🔙 Главное меню", "menu:main")]],
        )
        return

    await client.answer_callback(callback_id)


async def process_update(client: MaxBotClient, update: Dict[str, Any]):
    """Обработка одного входящего события из MAX Bot API."""
    update_type = update.get("update_type")
    logger.info(f"Получено событие типа: {update_type}")

    if update_type == "bot_started":
        user_info = update.get("user", {})
        user_id = user_info.get("user_id")
        if user_id:
            await handle_start_command(client, user_id, user_info)

    elif update_type == "message_created":
        msg = update.get("message", {})
        sender = msg.get("sender", {})
        user_id = sender.get("user_id")
        body = msg.get("body", {})
        text = body.get("text", "").strip()

        if not user_id:
            return

        # Всегда синхронизируем пользователя и его @тег из МАКС
        await register_or_get_user(sender)

        # Если пользователь отправляет тег через собачку напрямую (например: @polina или @alex_tutor)
        if text.startswith("@") and len(text) > 1 and " " not in text:
            cleaned_tag = text.lstrip("@").strip()
            async with AsyncSessionLocal() as session:
                user = await crud_user.get_by_telegram_id(session, user_id)
                if not user:
                    user = await register_or_get_user(sender)
                user.username = cleaned_tag
                await session.commit()

            await client.send_message(
                user_id=user_id,
                text=(
                    f"✅ Ваш контактный @тег успешно сохранен: **@{cleaned_tag}**!\n\n"
                    f"Теперь собеседники смогут сразу находить вас в поиске МАКС и переходить в чат с вами по прямой кнопке."
                ),
                buttons=[[btn_callback("🏠 Главное меню", "menu:main")]]
            )
            return

        # FSM состояния
        if user_id in user_fsm:
            st = user_fsm[user_id].get("state")
            if st in ("enter_username_for_task", "setting_tag_manually"):
                cleaned_tag = text.lstrip("@").strip()
                del user_fsm[user_id]
                async with AsyncSessionLocal() as session:
                    user = await crud_user.get_by_telegram_id(session, user_id)
                    if not user:
                        user = await register_or_get_user(sender)
                    user.username = cleaned_tag
                    await session.commit()

                await client.send_message(
                    user_id=user_id,
                    text=f"✅ Контакт @{cleaned_tag} сохранен в вашем профиле!"
                )
                if st == "enter_username_for_task":
                    await prompt_choose_block(client, user_id, cleaned_tag)
                else:
                    await handle_profile_view(client, user_id)
                return

            elif st == "waiting_telemost_link":
                handled = await handle_telemost_link_input(client, user_id, text, sender)
                if handled:
                    return
            elif st in ("relay_message", "active_chat_session"):
                handled = await handle_relay_text(client, user_id, text, sender)
                if handled:
                    return
            elif st == "checking_bank_answer":
                task_id = user_fsm[user_id]["data"]["task_id"]
                del user_fsm[user_id]
                async with AsyncSessionLocal() as session:
                    t = await crud_bank_task.get_by_id(session, task_id)

                if t:
                    u_clean = text.strip().lower().replace(",", ".")
                    c_clean = t.answer.strip().lower().replace(",", ".")
                    is_correct = (u_clean == c_clean)

                    if is_correct:
                        async with AsyncSessionLocal() as session:
                            u = await crud_user.get_by_telegram_id(session, user_id)
                            if u:
                                try:
                                    await award_xp(session, user_id=u.id, amount=15, reason=XPReason.BANK_SOLVED.value, task_id=t.id)
                                    await session.commit()
                                except Exception as e:
                                    logger.warning(f"Ошибка award_xp: {e}")
                        await client.send_message(
                            user_id=user_id,
                            text=(
                                f"🎉 Браво! Ваш ответ «{text}» абсолютно верный!\n\n"
                                f"Вам начислено +15 XP в рейтинг!\n\n"
                                f"Правильный ответ: {t.answer}"
                            ),
                            buttons=[
                                [btn_callback("📖 Показать полное решение", f"bank:sol:{t.id}")],
                                [btn_callback("🔙 К списку задач", f"bank:open_block:{t.grade}:{t.block}")],
                                [btn_callback("🏠 Главное меню", "menu:main")],
                            ]
                        )
                    else:
                        await client.send_message(
                            user_id=user_id,
                            text=(
                                f"❌ Ответ «{text}» не совпал с эталоном.\n\n"
                                f"Попробуйте пересчитать или воспользуйтесь подсказкой:"
                            ),
                            buttons=[
                                [btn_callback("💡 Подсказка", f"bank:hint:{t.id}"), btn_callback("✍️ Попробовать снова", f"bank:ans_prompt:{t.id}")],
                                [btn_callback("📖 Показать решение", f"bank:sol:{t.id}")],
                                [btn_callback("🔙 К задаче", f"bank:open_task:{t.id}")],
                            ]
                        )
                return

            elif st == "enter_question":
                handled = await handle_fsm_text_input(client, user_id, text, sender)
                if handled:
                    return

        # Текстовые и слэш-команды
        cmd = text.strip().lower()
        if cmd in ("/start", "старт", "start", "/menu", "меню", "menu", "/главная", "главная"):
            await handle_start_command(client, user_id, sender)
        elif cmd in ("/profile", "профиль", "profile", "/me"):
            await handle_profile_view(client, user_id)
        elif cmd in ("/telemost", "телемост", "telemost", "видео", "созвон"):
            await handle_telemost_tab(client, user_id)
        elif cmd in ("/tasks", "задачи", "tasks", "мои задачи", "/mytasks"):
            await handle_show_my_tasks(client, user_id)
        elif cmd in ("/cabinet", "кабинет", "/board", "доска", "преподаватель", "tutor"):
            await handle_show_tutor_board(client, user_id)
        elif cmd in ("/new", "создать", "новая", "/create"):
            await handle_start_create_task(client, user_id)
        elif cmd in ("/help", "помощь", "help", "/info", "инфо", "информация"):
            info_text = (
                "ℹ️ **Справка по боту физики ОГЭ (МАКС):**\n\n"
                "📌 **Команды бота (через слэш или текстом):**\n"
                "• /menu — Главное меню\n"
                "• /cabinet — Кабинет преподавателя (свежие задачи)\n"
                "• /tasks — Мои заявки на разбор\n"
                "• /telemost — Вкладка Яндекс Телемост\n"
                "• /profile — Личный профиль, звание и @тег\n"
                "• /new — Оставить новую заявку на разбор\n"
                "• /help — Данная справка\n\n"
                "💡 **Навигация:**\n"
                "Вы можете легко перемещаться с помощью кнопок под сообщениями (например, «🏠 Главное меню») или выбирать команды через слэш (/)."
            )
            await client.send_message(
                user_id=user_id,
                text=info_text,
                buttons=[[btn_callback("🏠 Главное меню", "menu:main")]]
            )
        else:
            await handle_start_command(client, user_id, sender)

    elif update_type == "message_callback":
        await process_callback(client, update)


# ==========================================================
# ОСНОВНОЙ ЦИКЛ LONG POLLING
# ==========================================================

async def main():
    token = settings.MAX_BOT_TOKEN
    if not token or len(token) < 20:
        print("\n" + "!" * 70)
        print("❌ ОШИБКА: Токен MAX_BOT_TOKEN не задан в .env!")
        print("!" * 70 + "\n")
        return

    await seed_topics()
    await seed_bank_tasks()

    client = MaxBotClient(token=token)

    try:
        bot_info = await client.get_me()
        bot_username = bot_info.get("username", "неизвестно")
        print("\n" + "=" * 65)
        print(f"🤖 БОТ МАКС УСПЕШНО ПОДКЛЮЧЕН К PLATFORM-API2.MAX.RU!")
        print(f"Имя бота: {bot_info.get('name')} (@{bot_username})")
        print(f"Ссылка на бота: https://max.ru/{bot_username}")
        print("Вкладка «Телемост» и парсинг @тегов пользователей активны!")
        print("=" * 65 + "\n")
    except Exception as e:
        print(f"❌ Ошибка подключения к MAX API: {e}")
        await client.close()
        return

    marker = None
    logger.info("Запуск цикла Long Polling...")

    try:
        while True:
            try:
                data = await client.get_updates(marker=marker, timeout=25)
                updates = data.get("updates", [])
                marker = data.get("marker", marker)

                for update in updates:
                    try:
                        await process_update(client, update)
                    except Exception as e:
                        logger.error(f"Ошибка при обработке update: {e}", exc_info=True)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле Long Polling: {e}")
                await asyncio.sleep(3)
    finally:
        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен.")
