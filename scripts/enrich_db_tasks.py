import sqlite3

con = sqlite3.connect('/var/www/oge_physics/oge_physics.db')
cur = con.cursor()

# 1. Update task 1
cur.execute('''
UPDATE tasks SET 
teacher_response = ?
WHERE id = 1
''', (
"""Решение задания №24 (ОГЭ, Часть 2):

1) Полезная работа подъема груза на высоту h:
   A_пол = m · g · h = 30 кг · 10 Н/кг · 1,5 м = 450 Дж.
2) Затраченная работа силы тяги F вдоль плоскости длины L:
   A_затр = F · L = 120 Н · 5 м = 600 Дж.
3) Коэффициент полезного действия:
   η = (A_пол / A_затр) · 100% = (450 / 600) · 100% = 75%.
4) Сила трения: A_тр = A_затр - A_пол = 150 Дж => F_тр = 150 / 5 = 30 Н.

Ответ: КПД равен 75%, сила трения 30 Н.""",
))

# 2. Update task 3
cur.execute('''
UPDATE tasks SET 
teacher_response = ?
WHERE id = 3
''', (
"""Разбор задачи на сообщающиеся сосуды и закон Архимеда:

1) Условие гидростатического равновесия на уровне границы раздела жидкостей:
   p1 = p2  =>  ρ_в · g · h_в = ρ_к · g · h_к.
2) Отношение высот столбов разнородных жидкостей обратно пропорционально плотностям:
   h_в / h_к = ρ_к / ρ_в = 800 / 1000 = 0.8.
3) При высоте керосина 20 см, столб воды поднимется на:
   h_в = 0.8 · 20 см = 16 см.

Ответ: уровень воды поднимется на 16 см.""",
))

# 3. Add 7th grade task
cur.execute("SELECT id FROM tasks WHERE grade = 7 AND status = 'COMPLETED'")
if not cur.fetchone():
    cur.execute('''
    INSERT INTO tasks (
        student_id, tutor_id, topic_id, grade, part, photo_url, question, 
        scheduled_time, status, request_type, teacher_response, created_at, updated_at
    ) VALUES (
        1, 2, 2, 7, 'PART_1', '', 
        'Как рассчитать массу дубовой балки объемом 0.04 м³, если плотность дуба 700 кг/м³?',
        'Сегодня', 'COMPLETED', 'TASK',
        'Дано: V = 0,04 м³, ρ = 700 кг/м³.\\n\\n1) Основная формула связи массы, объема и плотности:\\n   m = ρ · V\\n2) Вычисление в СИ:\\n   m = 700 кг/м³ · 0,04 м³ = 28 кг.\\n\\nОтвет: масса балки равна 28 кг.',
        datetime('now', '-2 days'), datetime('now', '-1 days')
    )
    ''')

# 4. Add 8th grade task
cur.execute("SELECT id FROM tasks WHERE grade = 8 AND status = 'COMPLETED'")
if not cur.fetchone():
    cur.execute('''
    INSERT INTO tasks (
        student_id, tutor_id, topic_id, grade, part, photo_url, question, 
        scheduled_time, status, request_type, teacher_response, created_at, updated_at
    ) VALUES (
        1, 2, 8, 8, 'PART_1', '', 
        'Какое количество теплоты выделится при охлаждении медного радиатора массой 500 г от 380 °C до 80 °C?',
        'Сегодня', 'COMPLETED', 'TASK',
        'Дано: m = 500 г = 0,5 кг, t1 = 380 °C, t2 = 80 °C, c = 400 Дж/(кг·°C).\\n\\n1) Изменение температуры:\\n   Δt = t1 - t2 = 380 - 80 = 300 °C\\n2) Формула количества теплоты:\\n   Q = c · m · Δt\\n3) Вычисления:\\n   Q = 400 · 0,5 · 300 = 60 000 Дж = 60 кДж.\\n\\nОтвет: выделится 60 кДж теплоты.',
        datetime('now', '-1 days'), datetime('now')
    )
    ''')

con.commit()
print('Tasks enriched successfully!')
con.close()
