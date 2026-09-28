import sqlite3
from datetime import datetime, timedelta

con = sqlite3.connect('/var/www/oge_physics/oge_physics.db')
cur = con.cursor()

# 1. Create or get System User
cur.execute("SELECT id FROM users WHERE username = 'oge_system' OR telegram_id = 999999999")
sys_user = cur.fetchone()
if not sys_user:
    cur.execute("""
    INSERT INTO users (telegram_id, active_role, base_role, first_name, username, xp, level, created_at, updated_at)
    VALUES (999999999, 'tutor', 'tutor', 'Система', 'oge_system', 5000, '⭐ Эксперт', datetime('now'), datetime('now'))
    """)
    system_user_id = cur.lastrowid
else:
    system_user_id = sys_user[0]
    cur.execute("UPDATE users SET first_name = 'Система', username = 'oge_system' WHERE id = ?", (system_user_id,))

# Ensure student user exists
cur.execute("SELECT id FROM users WHERE active_role = 'student' OR base_role = 'student' LIMIT 1")
student_row = cur.fetchone()
if not student_row:
    cur.execute("""
    INSERT INTO users (telegram_id, active_role, base_role, first_name, username, xp, level, created_at, updated_at)
    VALUES (111111111, 'student', 'student', 'Ученик', 'student_demo', 100, 'Новичок', datetime('now'), datetime('now'))
    """)
    student_user_id = cur.lastrowid
else:
    student_user_id = student_row[0]

# 2. Get topic IDs by titles/blocks
def get_topic_id(grade, search_term, fallback_block):
    cur.execute("SELECT id FROM topics WHERE grade = ? AND (title LIKE ? OR block = ?) ORDER BY id LIMIT 1",
                (grade, f"%{search_term}%", fallback_block))
    r = cur.fetchone()
    if r:
        return r[0]
    cur.execute("SELECT id FROM topics WHERE grade = ? LIMIT 1", (grade,))
    r2 = cur.fetchone()
    return r2[0] if r2 else 1

topic_7_vessels = get_topic_id(7, 'сообща', 'PRESSURE_7')
topic_7_lever = get_topic_id(7, 'рычаг', 'WORK_7')
topic_8_ohm = get_topic_id(8, 'Ом', 'ELECTRODYNAMICS')
topic_8_resistors = get_topic_id(8, 'соединени', 'ELECTRODYNAMICS')
topic_9_kinematics = get_topic_id(9, 'равномерн', 'MECHANICS')

print(f"Mapped Topics: 7vessels={topic_7_vessels}, 7lever={topic_7_lever}, 8ohm={topic_8_ohm}, 8resistors={topic_8_resistors}, 9kinematics={topic_9_kinematics}")

# 3. Clean existing tasks
print("Cleaning old tasks...")
cur.execute("DELETE FROM tasks")

# 4. Insert 5 real tasks from A. V. Peryshkin textbook
tasks_data = [
    {
        "grade": 7,
        "topic_id": topic_7_vessels,
        "part": "PART_1",
        "photo_url": "/uploads/tasks/peryshkin_ris56.png",
        "question": "В U-образную трубку налиты ртуть, вода и керосин (рис. 56). Высота столба воды равна 20 см, а уровень ртути в обоих сосудах одинаков. Какова высота слоя керосина?",
        "teacher_response": """📖 Автор задачи: А. В. Перышкин («Сборник задач по физике 7–9 классы», № 437)

Дано:
• h_в = 20 см = 0,2 м
• ρ_в = 1000 кг/м³ (плотность воды)
• ρ_к = 800 кг/м³ (плотность керосина)
• Уровень ртути в обоих коленах одинаков: h_рт1 = h_рт2

Решение:
1) Согласно закону сообщающихся сосудов, на одном горизонтальном уровне в однородной покоящейся жидкости давление одинаково.
2) Так как уровень ртути в обоих коленах одинаков, гидростатические давления столба воды и столба керосина на границе с ртутью должны быть равны:
   p_в = p_к

3) Запишем формулу гидростатического давления столба жидкости:
   p = ρ · g · h
   ρ_в · g · h_в = ρ_к · g · h_к

4) Сокращаем g и выражаем высоту столба керосина h_к:
   h_к = (ρ_в · h_в) / ρ_к

5) Подставляем значения:
   h_к = (1000 кг/м³ · 20 см) / 800 кг/м³ = 25 см = 0,25 м.

Ответ: высота слоя керосина составляет 25 см (0,25 м).""",
        "days_ago": 3,
    },
    {
        "grade": 8,
        "topic_id": topic_8_ohm,
        "part": "PART_1",
        "photo_url": "/uploads/tasks/peryshkin_ris104.png",
        "question": "Используя график зависимости силы тока от напряжения (рис. 104), найдите электрическое сопротивление проводника.",
        "teacher_response": """📖 Автор задачи: А. В. Перышкин («Сборник задач по физике 7–9 классы», № 1028)

Дано:
• По графику на рис. 104:
  при напряжении U = 4 В сила тока I = 2 А
  при напряжении U = 2 В сила тока I = 1 А

Решение:
1) График представляет собой линейную вольт-амперную характеристику, выходящую из начала координат, что соответствует закону Ома для участка цепи:
   I = U / R

2) Выразим электрическое сопротивление проводника R:
   R = U / I

3) Подставим значения из выбранной точки графика (U = 4 В, I = 2 А):
   R = 4 В / 2 А = 2 Ом.

4) Проверка по второй точке (U = 2 В, I = 1 А):
   R = 2 В / 1 А = 2 Ом.
   Сопротивление проводника неизменно.

Ответ: электрическое сопротивление проводника равно 2 Ом.""",
        "days_ago": 2,
    },
    {
        "grade": 9,
        "topic_id": topic_9_kinematics,
        "part": "PART_1",
        "photo_url": "/uploads/tasks/peryshkin_ris14.png",
        "question": "По графику зависимости пути от времени (рис. 14) определите скорость тела при равномерном движении (в м/с).",
        "teacher_response": """📖 Автор задачи: А. В. Перышкин («Сборник задач по физике 7–9 классы», № 143)

Дано:
• По графику на рис. 14:
  за время t = 4 мин пройден путь s = 600 м
  (или за время t = 2 мин пройден путь s = 300 м)

Решение:
1) Переведем время в Международную систему единиц (СИ):
   t = 4 мин = 4 · 60 с = 240 с.

2) График зависимости пути s от времени t — прямая линия, выходящая из начала координат (0, 0). Это означает, что тело движется равномерно и прямолинейно с постоянной скоростью:
   v = const.

3) Формула скорости равномерного прямолинейного движения:
   v = s / t

4) Подставляем значения пути и времени:
   v = 600 м / 240 с = 2,5 м/с.

Ответ: скорость тела при равномерном движении равна 2,5 м/с.""",
        "days_ago": 2,
    },
    {
        "grade": 8,
        "topic_id": topic_8_resistors,
        "part": "PART_1",
        "photo_url": "/uploads/tasks/peryshkin_ris106.png",
        "question": "На рисунке 106 изображена электрическая цепь с сопротивлениями R1 = 1 Ом, R2 = 5 Ом, R3 = 4 Ом, R4 = 3 Ом. Каково общее сопротивление цепи?",
        "teacher_response": """📖 Автор задачи: А. В. Перышкин («Сборник задач по физике 7–9 классы», № 1084)

Дано:
• R1 = 1 Ом
• R2 = 5 Ом
• R3 = 4 Ом
• R4 = 3 Ом

Решение:
1) Проанализируем схему на рисунке 106: все четыре резистора соединены друг за другом последовательно, ток протекает по единой цепи без ветвления.
2) При последовательном соединении общее электрическое сопротивление цепи равно сумме сопротивлений каждого участка:
   R_общ = R1 + R2 + R3 + R4

3) Вычисляем сумму сопротивлений:
   R_общ = 1 Ом + 5 Ом + 4 Ом + 3 Ом = 13 Ом.

Ответ: общее сопротивление цепи равно 13 Ом.""",
        "days_ago": 1,
    },
    {
        "grade": 7,
        "topic_id": topic_7_lever,
        "part": "PART_1",
        "photo_url": "/uploads/tasks/peryshkin_ris71.png",
        "question": "Большая и маленькая гири уравновешены на невесомом рычаге (рис. 71). Отношение плеч рычага 1 : 5. Масса большой гири 2,5 кг. Найдите массу меньшей гири.",
        "teacher_response": """📖 Автор задачи: А. В. Перышкин («Сборник задач по физике 7–9 классы», № 581)

Дано:
• m1 = 2,5 кг (масса большой гири)
• Отношение плеч рычага: l1 / l2 = 1 / 5  =>  l2 = 5 · l1

Решение:
1) Условие равновесия рычага (правило моментов сил):
   F1 · l1 = F2 · l2

2) Силы, действующие на концы рычага, равны силам тяжести подвешенных гирь:
   F1 = m1 · g,   F2 = m2 · g
   m1 · g · l1 = m2 · g · l2  =>  m1 · l1 = m2 · l2

3) Выразим массу меньшей гири m2:
   m2 = m1 · (l1 / l2)

4) Вычисляем:
   m2 = 2,5 кг · (1 / 5) = 0,5 кг = 500 г.

Ответ: масса меньшей гири равна 0,5 кг (500 г).""",
        "days_ago": 1,
    },
]

for t in tasks_data:
    created = datetime.now() - timedelta(days=t["days_ago"])
    updated = created + timedelta(hours=2)
    cur.execute("""
    INSERT INTO tasks (
        student_id, tutor_id, topic_id, grade, part, photo_url, question, 
        scheduled_time, status, request_type, teacher_response, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Сегодня', 'COMPLETED', 'TASK', ?, ?, ?)
    """, (
        student_user_id,
        system_user_id,
        t["topic_id"],
        t["grade"],
        t["part"],
        t["photo_url"],
        t["question"],
        t["teacher_response"],
        created.strftime('%Y-%m-%d %H:%M:%S'),
        updated.strftime('%Y-%m-%d %H:%M:%S'),
    ))

con.commit()
cur.execute("SELECT count(*) FROM tasks")
print(f"Tasks inserted! Total tasks count: {cur.fetchone()[0]}")
con.close()
