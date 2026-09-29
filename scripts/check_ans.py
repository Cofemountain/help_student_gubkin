import sqlite3

con = sqlite3.connect('/var/www/oge_physics/oge_physics.db')
cur = con.cursor()
for r in cur.execute("SELECT id, title, answer, difficulty FROM bank_tasks WHERE bank_type = 'CLOSED'"):
    print(r)
con.close()
