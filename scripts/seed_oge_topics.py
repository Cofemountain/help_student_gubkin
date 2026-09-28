import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, Base, engine
from app.models.topic import Topic, OGEBlock

OGE_TOPICS_SEED = [
    # РАЗДЕЛ 1: МЕХАНИЧЕСКИЕ ЯВЛЕНИЯ
    {
        "block": OGEBlock.MECHANICS.value,
        "sort_order": 1,
        "title": "Равноускоренное движение, ускорение, графики движения",
    },
    {
        "block": OGEBlock.MECHANICS.value,
        "sort_order": 2,
        "title": "Законы Ньютона, силы тяжести, упругости, трения",
    },
    {
        "block": OGEBlock.MECHANICS.value,
        "sort_order": 3,
        "title": "Закон сохранения импульса и энергии, работа и мощность",
    },
    {
        "block": OGEBlock.MECHANICS.value,
        "sort_order": 4,
        "title": "Статика: условия равновесия рычага, КПД простых механизмов",
    },
    {
        "block": OGEBlock.MECHANICS.value,
        "sort_order": 5,
        "title": "Давление в жидкостях и газах, сила Архимеда, плавание тел",
    },
    {
        "block": OGEBlock.MECHANICS.value,
        "sort_order": 6,
        "title": "Механические колебания и волны, звук",
    },

    # РАЗДЕЛ 2: ТЕПЛОВЫЕ ЯВЛЕНИЯ
    {
        "block": OGEBlock.THERMODYNAMICS.value,
        "sort_order": 7,
        "title": "Теплопередача, количество теплоты, удельная теплоемкость",
    },
    {
        "block": OGEBlock.THERMODYNAMICS.value,
        "sort_order": 8,
        "title": "Фазовые переходы: плавление, кипение, влажность воздуха",
    },
    {
        "block": OGEBlock.THERMODYNAMICS.value,
        "sort_order": 9,
        "title": "Уравнение теплового баланса и КПД тепловых двигателей",
    },

    # РАЗДЕЛ 3: ЭЛЕКТРОМАГНИТНЫЕ ЯВЛЕНИЯ
    {
        "block": OGEBlock.ELECTRODYNAMICS.value,
        "sort_order": 10,
        "title": "Электрические цепи: последовательное и параллельное соединение, Закон Ома",
    },
    {
        "block": OGEBlock.ELECTRODYNAMICS.value,
        "sort_order": 11,
        "title": "Работа и мощность тока, Закон Джоуля-Ленца",
    },
    {
        "block": OGEBlock.ELECTRODYNAMICS.value,
        "sort_order": 12,
        "title": "Магнитное поле, электромагнитная индукция, опыты Фарадея",
    },
    {
        "block": OGEBlock.ELECTRODYNAMICS.value,
        "sort_order": 13,
        "title": "Геометрическая оптика: отражение, преломление, построение в линзах",
    },

    # РАЗДЕЛ 4: КВАНТОВЫЕ ЯВЛЕНИЯ
    {
        "block": OGEBlock.QUANTUM.value,
        "sort_order": 14,
        "title": "Строение атома и атомного ядра, изотопы",
    },
    {
        "block": OGEBlock.QUANTUM.value,
        "sort_order": 15,
        "title": "Радиоактивность: альфа, бета, гамма-излучения, ядерные реакции",
    },

    # РАЗДЕЛ 5: ВТОРАЯ ЧАСТЬ ОГЭ (ПОВЫШЕННАЯ СЛОЖНОСТЬ)
    {
        "block": OGEBlock.PART_2_ADVANCED.value,
        "sort_order": 16,
        "title": "Качественные задачи с подробным объяснением (№20–22 ОГЭ)",
    },
    {
        "block": OGEBlock.PART_2_ADVANCED.value,
        "sort_order": 17,
        "title": "Расчетные комбинированные задачи 2-й части (№23–25 ОГЭ)",
    },
]


async def seed_topics() -> int:
    """Создает таблицы и наполняет кодификатор тем ОГЭ."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        inserted_count = 0
        for item in OGE_TOPICS_SEED:
            result = await session.execute(
                select(Topic).where(Topic.title == item["title"])
            )
            existing = result.scalar_one_or_none()
            if not existing:
                topic = Topic(
                    block=item["block"],
                    sort_order=item["sort_order"],
                    title=item["title"],
                    is_active=True,
                )
                session.add(topic)
                inserted_count += 1

        await session.commit()
        print(f"✅ База данных инициализирована. Добавлено новых тем ОГЭ: {inserted_count} (всего в кодификаторе: {len(OGE_TOPICS_SEED)})")
        return inserted_count


if __name__ == "__main__":
    asyncio.run(seed_topics())
