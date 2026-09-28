"""
Сервис push-уведомлений через MAX Bot API.
Мост между FastAPI (Mini App) и ботом МАКС.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from app.core.config import settings

logger = logging.getLogger("NOTIFICATIONS")
MAX_API_BASE = "https://platform-api2.max.ru"


class MaxNotifier:
    def __init__(self, token: str):
        self.token = token
        self.headers = {"Authorization": token, "Content-Type": "application/json"}
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        return self._session

    async def send(self, user_id: int, text: str, buttons: Optional[List[List[Dict[str, Any]]]] = None) -> bool:
        if not self.token or len(self.token) < 20:
            logger.warning("MAX_BOT_TOKEN не задан, уведомление пропущено.")
            return False
        session = await self._get_session()
        body: Dict[str, Any] = {"text": text}
        if buttons:
            body["attachments"] = [{"type": "inline_keyboard", "payload": {"buttons": buttons}}]
        try:
            async with session.post(f"{MAX_API_BASE}/messages", headers=self.headers, params={"user_id": user_id}, json=body) as resp:
                if resp.status in (200, 201):
                    return True
                logger.warning(f"send error ({resp.status}) user_id={user_id}: {await resp.text()}")
                return False
        except Exception as exc:
            logger.error(f"send exception: {exc}")
            return False

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


_notifier: Optional[MaxNotifier] = None


def get_notifier() -> MaxNotifier:
    global _notifier
    if _notifier is None:
        _notifier = MaxNotifier(token=settings.MAX_BOT_TOKEN or "")
    return _notifier


def _btn_cb(text: str, payload: str) -> Dict[str, Any]:
    return {"type": "callback", "text": text, "payload": payload}


def _btn_link(text: str, url: str) -> Dict[str, Any]:
    return {"type": "link", "text": text, "url": url}


async def notify_task_accepted(
    student_tg_id: int, tutor_tg_id: int, task_id: int,
    topic_title: str, student_name: str, tutor_name: str,
    scheduled_time: Optional[str],
    tutor_username: Optional[str] = None, student_username: Optional[str] = None,
):
    notifier = get_notifier()

    s_text = (
        f"✨ Ваша заявка #{task_id} принята в работу!\n\n"
        f"👨‍🏫 Преподаватель: {tutor_name}\n"
        f"📚 Раздел: {topic_title}\n"
        f"🕒 Срок разбора: {scheduled_time or 'В ближайшее время'}\n\n"
        f"Преподаватель готовит решение или созвон. После проверки вы сможете закрыть заявку или задать вопрос."
    )
    s_buttons: List[List[Dict[str, Any]]] = [
        [_btn_cb("✅ Всё понятно, вопрос решён", f"solved:{task_id}")]
    ]

    t_text = (
        f"🤝 Вы взяли заявку #{task_id} на разбор!\n\n"
        f"👤 Обучающийся: {student_name}\n"
        f"📚 Раздел: {topic_title}\n"
        f"🕒 Срок: {scheduled_time or 'В ближайшее время'}\n\n"
        f"Подготовьте методический разбор в приложении или создайте комнату для созвона:"
    )
    t_buttons: List[List[Dict[str, Any]]] = [
        [_btn_cb("📹 Создать видеозвонок", f"telemost:{task_id}")]
    ]

    await asyncio.gather(notifier.send(student_tg_id, s_text, s_buttons), notifier.send(tutor_tg_id, t_text, t_buttons))
    logger.info(f"[notify] task={task_id} accepted: s={student_tg_id}, t={tutor_tg_id}")


async def notify_review_submitted(
    student_tg_id: int, task_id: int, topic_title: str, tutor_name: str,
    teacher_response: Optional[str], telemost_url: Optional[str],
    tutor_username: Optional[str] = None,
):
    notifier = get_notifier()

    if telemost_url:
        text = (
            f"📹 Видеоконсультация по заявке #{task_id} готова!\n\n"
            f"👨‍🏫 Преподаватель: {tutor_name}\n"
            f"📚 Раздел: {topic_title}\n\n"
            f"Комната в Яндекс Телемосте создана. Подключайтесь к видеоразбору:"
        )
        buttons: List[List[Dict[str, Any]]] = [
            [_btn_link("📹 Подключиться к видеовстрече", telemost_url)],
            [_btn_cb("✅ Всё понятно, вопрос решён", f"solved:{task_id}")],
        ]
    elif teacher_response:
        preview = teacher_response[:250] + ("..." if len(teacher_response) > 250 else "")
        text = (
            f"📝 Разбор задачи #{task_id} готов!\n\n"
            f"👨‍🏫 Преподаватель: {tutor_name}\n"
            f"📚 Раздел: {topic_title}\n\n"
            f"📖 Пояснение и формулы:\n"
            f"{preview}\n\n"
            f"Ознакомьтесь с разбором в приложении. Если всё понятно — закройте заявку, если нет — напишите уточнение."
        )
        buttons = [
            [_btn_cb("✅ Всё понятно, вопрос решён", f"solved:{task_id}")]
        ]
    else:
        return

    await notifier.send(student_tg_id, text, buttons)
    logger.info(f"[notify] task={task_id} review: s={student_tg_id}")


async def notify_task_completed(
    tutor_tg_id: int, task_id: int, topic_title: str, student_name: str, tutor_xp: int = 100,
):
    notifier = get_notifier()
    text = (
        f"🎉 Заявка #{task_id} успешно решена!\n\n"
        f"👤 Обучающийся {student_name} подтвердил понимание материала.\n"
        f"📚 Раздел: {topic_title}\n"
        f"⭐️ Начислено: +{tutor_xp} XP\n\n"
        f"Спасибо за ваш вклад! Педагогический рейтинг наставника повышен."
    )
    buttons = [[_btn_cb("🏆 Мой профиль и звание", "menu:profile")], [_btn_cb("📋 Новые заявки", "menu:tutor_board")]]
    await notifier.send(tutor_tg_id, text, buttons)
    logger.info(f"[notify] task={task_id} completed: t={tutor_tg_id}")


async def notify_new_task_to_tutors(
    tutor_tg_ids: List[int], task_id: int, topic_title: str,
    student_name: str, question: str, scheduled_time: Optional[str],
):
    if not tutor_tg_ids:
        return
    notifier = get_notifier()
    q_preview = question[:160] + ("..." if len(question) > 160 else "")
    text = (
        f"⚡ Новая заявка на разбор #{task_id}!\n\n"
        f"👤 Ученик: {student_name}\n"
        f"📚 Тема: {topic_title}\n"
        f"🕒 Срок: {scheduled_time or 'Как можно скорее'}\n\n"
        f"❓ Вопрос:\n{q_preview}\n\n"
        f"Нажмите «Взять на разбор», чтобы помочь ученику (+25 XP)!"
    )
    buttons = [[_btn_cb("🤝 Взять заявку", f"accept:{task_id}")], [_btn_cb("📋 Все заявки", "menu:tutor_board")]]
    results = await asyncio.gather(*[notifier.send(tg_id, text, buttons) for tg_id in tutor_tg_ids], return_exceptions=True)
    logger.info(f"[notify] task={task_id}: broadcast to {sum(1 for r in results if r is True)}/{len(tutor_tg_ids)} tutors")


async def notify_student_clarification(
    tutor_tg_id: int,
    task_id: int,
    topic_title: str,
    student_name: str,
    clarification: str,
):
    notifier = get_notifier()
    text = (
        f"❓ Уточняющий вопрос от ученика #{task_id}!\n\n"
        f"👤 Обучающийся: {student_name}\n"
        f"📚 Раздел: {topic_title}\n\n"
        f"💬 Что осталось непонятно:\n«{clarification}»\n\n"
        f"👉 Откройте карточку заявки на платформе, чтобы дополнить разбор."
    )
    buttons = [[_btn_cb("📋 Открыть заявки", "menu:tutor_board")]]
    await notifier.send(tutor_tg_id, text, buttons)
    logger.info(f"[notify] task={task_id} clarification from {student_name} to tutor={tutor_tg_id}")
