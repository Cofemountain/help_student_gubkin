import sqlite3
import os
import sys

def migrate(db_path: str):
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Add grade column to tasks if missing
    task_cols = [c[1] for c in cur.execute("PRAGMA table_info(tasks)").fetchall()]
    if "grade" not in task_cols:
        print("Adding grade column to tasks...")
        cur.execute("ALTER TABLE tasks ADD COLUMN grade INTEGER NOT NULL DEFAULT 9")
        conn.commit()

    if "solution_photo_url" not in task_cols:
        print("Adding solution_photo_url column to tasks...")
        cur.execute("ALTER TABLE tasks ADD COLUMN solution_photo_url TEXT NOT NULL DEFAULT ''")
        conn.commit()

    if "student_clarification" not in task_cols:
        print("Adding student_clarification column to tasks...")
        cur.execute("ALTER TABLE tasks ADD COLUMN student_clarification TEXT NOT NULL DEFAULT ''")
        conn.commit()

    # 2. Add grade column to topics if missing
    topic_cols = [c[1] for c in cur.execute("PRAGMA table_info(topics)").fetchall()]
    if "grade" not in topic_cols:
        print("Adding grade column to topics...")
        cur.execute("ALTER TABLE topics ADD COLUMN grade INTEGER NOT NULL DEFAULT 9")
        conn.commit()

    # 3. Comprehensive topics list for 7, 8, 9 grades and OGE
    ALL_TOPICS = [
        # --- 7 КЛАСС ---
        (7, "MECHANICS_7", "Механическое движение. Траектория, путь, скорость и средняя скорость", 1),
        (7, "MECHANICS_7", "Масса тела. Измерение массы на весах", 2),
        (7, "MECHANICS_7", "Плотность вещества и расчет массы и объема тела", 3),
        (7, "FORCES_7", "Сила тяжести и явление всемирного тяготения", 4),
        (7, "FORCES_7", "Сила упругости. Закон Гука и динамометр", 5),
        (7, "FORCES_7", "Вес тела и состояние невесомости", 6),
        (7, "FORCES_7", "Сила трения (покоя, скольжения, качения)", 7),
        (7, "PRESSURE_7", "Давление твердых тел. Способы увеличения и уменьшения давления", 8),
        (7, "PRESSURE_7", "Давление в жидкостях и газах. Закон Паскаля", 9),
        (7, "PRESSURE_7", "Сообщающиеся сосуды и гидравлический пресс", 10),
        (7, "PRESSURE_7", "Атмосферное давление. Опыт Торричелли и барометр", 11),
        (7, "PRESSURE_7", "Сила Архимеда (выталкивающая сила) и плавание тел", 12),
        (7, "WORK_7", "Механическая работа и мощность", 13),
        (7, "WORK_7", "Простые механизмы: рычаг и правило равновесия рычага", 14),
        (7, "WORK_7", "Момент силы и условия равновесия твердого тела", 15),
        (7, "WORK_7", "Блоки (подвижный и неподвижный), наклонная плоскость", 16),
        (7, "WORK_7", "Коэффициент полезного действия (КПД) механизмов", 17),

        # --- 8 КЛАСС ---
        (8, "THERMODYNAMICS", "Внутренняя энергия и способы ее изменения", 20),
        (8, "THERMODYNAMICS", "Виды теплопередачи: теплопроводность, конвекция, излучение", 21),
        (8, "THERMODYNAMICS", "Количество теплоты. Удельная теплоемкость вещества", 22),
        (8, "THERMODYNAMICS", "Удельная теплота сгорания топлива", 23),
        (8, "THERMODYNAMICS", "Плавление и кристаллизация. Удельная теплота плавления", 24),
        (8, "THERMODYNAMICS", "Испарение, конденсация и кипение. Удельная теплота парообразования", 25),
        (8, "THERMODYNAMICS", "Влажность воздуха. Психрометр", 26),
        (8, "THERMODYNAMICS", "Тепловые двигатели и КПД теплового двигателя", 27),
        (8, "ELECTRODYNAMICS", "Электризация тел. Два рода зарядов. Закон сохранения заряда", 28),
        (8, "ELECTRODYNAMICS", "Строение атома. Электрон, ионы. Проводники и диэлектрики", 29),
        (8, "ELECTRODYNAMICS", "Электрический ток. Источники тока и электрическая цепь", 30),
        (8, "ELECTRODYNAMICS", "Сила тока, амперметр. Электрическое напряжение, вольтметр", 31),
        (8, "ELECTRODYNAMICS", "Электрическое сопротивление проводников. Удельное сопротивление", 32),
        (8, "ELECTRODYNAMICS", "Закон Ома для участка электрической цепи", 33),
        (8, "ELECTRODYNAMICS", "Последовательное и параллельное соединение проводников", 34),
        (8, "ELECTRODYNAMICS", "Работа и мощность электрического тока", 35),
        (8, "ELECTRODYNAMICS", "Закон Джоуля-Ленца и тепловое действие тока", 36),
        (8, "MAGNETISM_8", "Магнитное поле прямого проводника и катушки с током", 37),
        (8, "MAGNETISM_8", "Электромагниты и их практическое применение", 38),
        (8, "MAGNETISM_8", "Постоянные магниты. Магнитное поле Земли", 39),
        (8, "MAGNETISM_8", "Действие магнитного поля на проводник с током. Электродвигатель", 40),
        (8, "OPTICS_8", "Прямолинейное распространение света. Закон отражения света", 41),
        (8, "OPTICS_8", "Плоское зеркало. Построение изображения в зеркале", 42),
        (8, "OPTICS_8", "Преломление света. Закон преломления", 43),
        (8, "OPTICS_8", "Линзы (собирающая и рассеивающая). Оптическая сила линзы", 44),
        (8, "OPTICS_8", "Построение изображений в тонких линзах. Формула линзы", 45),

        # --- 9 КЛАСС + ОГЭ ---
        (9, "MECHANICS", "Материальная точка, перемещение, равноускоренное прямолинейное движение", 50),
        (9, "MECHANICS", "Законы Ньютона, силы в механике, равновесие", 51),
        (9, "MECHANICS", "Свободное падение тел. Движение тела по окружности", 52),
        (9, "MECHANICS", "Импульс тела. Закон сохранения импульса. Реактивное движение", 53),
        (9, "MECHANICS", "Закон сохранения механической энергии, работа и мощность", 54),
        (9, "WAVES_9", "Колебательное движение. Период, частота, маятники", 55),
        (9, "WAVES_9", "Механические волны и звук. Скорость и длина волны", 56),
        (9, "ELECTROMAGNETISM_9", "Магнитное поле, вектор магнитной индукции. Сила Ампера и Лоренца", 57),
        (9, "ELECTROMAGNETISM_9", "Электромагнитная индукция. Закон Фарадея и правило Ленца", 58),
        (9, "ELECTROMAGNETISM_9", "Электромагнитное поле и электромагнитные волны", 59),
        (9, "QUANTUM", "Строение атома и атомного ядра. Опыт Резерфорда, изотопы", 60),
        (9, "QUANTUM", "Радиоактивность. Закон радиоактивного распада, ядерные реакции", 61),
        # В дополнение темы ОГЭ (для 9 класса):
        (9, "OGE_PREP", "ОГЭ №20–22: Качественные задачи с развернутым объяснением явлений", 62),
        (9, "OGE_PREP", "ОГЭ №17: Экспериментальные задания, измерения и погрешности", 63),
        (9, "OGE_PREP", "ОГЭ №23–25: Расчетные комбинированные задачи повышенной сложности", 64),
        (9, "OGE_PREP", "ОГЭ №19: Анализ физических текстов и табличных данных", 65),
        (9, "OGE_PREP", "ОГЭ Комплексный разбор типового экзаменационного варианта (КИМ)", 66),
    ]

    # Insert or update
    for grade, block, title, sort_order in ALL_TOPICS:
        cur.execute("SELECT id FROM topics WHERE title = ?", (title,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE topics SET grade = ?, block = ?, sort_order = ?, is_active = 1 WHERE id = ?", (grade, block, sort_order, row[0]))
        else:
            cur.execute("INSERT INTO topics (grade, block, title, sort_order, is_active) VALUES (?, ?, ?, ?, 1)", (grade, block, title, sort_order))

    # Also update existing legacy topics grade to 9
    cur.execute("UPDATE topics SET grade = 9 WHERE grade IS NULL OR grade = 0")
    cur.execute("UPDATE tasks SET grade = 9 WHERE grade IS NULL OR grade = 0")
    conn.commit()

    total_topics = cur.execute("SELECT count(*) FROM topics").fetchone()[0]
    print(f"Migration completed. Total topics in database: {total_topics}")
    conn.close()

if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else "oge_physics.db"
    migrate(db)
