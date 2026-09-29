import sqlite3

con = sqlite3.connect('/var/www/oge_physics/oge_physics.db')
cur = con.cursor()
print("Homeworks:")
for r in cur.execute("SELECT id, task_id, bank_task_id, status FROM homeworks").fetchall():
    print(r)
print("Updating bank_tasks answers for calorimeter:")
cur.execute("UPDATE bank_tasks SET answer = '19.8' WHERE title LIKE '%калориметр%'")
con.commit()
for r in cur.execute("SELECT id, title, answer FROM bank_tasks WHERE title LIKE '%калориметр%'").fetchall():
    print(r)
con.close()
