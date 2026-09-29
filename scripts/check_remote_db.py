import sqlite3

con = sqlite3.connect('/var/www/oge_physics/oge_physics.db')
cur = con.cursor()
rows = cur.execute('SELECT id, student_id, tutor_id, status, request_type, telemost_url FROM tasks').fetchall()
print("Tasks count:", len(rows))
for r in rows:
    print(r)
