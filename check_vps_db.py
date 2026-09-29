import sqlite3

conn = sqlite3.connect('/var/www/oge_physics/oge_physics.db')
cur = conn.cursor()
tasks = cur.execute('SELECT id, student_id, tutor_id, status, question FROM tasks').fetchall()
print(f"Total tasks: {len(tasks)}")
for t in tasks:
    print(t)

users = cur.execute('SELECT id, telegram_id, active_role, first_name, username FROM users').fetchall()
print(f"Total users: {len(users)}")
for u in users:
    print(u)
