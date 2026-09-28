import sqlite3
con = sqlite3.connect('/var/www/oge_physics/oge_physics.db')
cur = con.cursor()
cur.execute("SELECT id, telegram_id, role, first_name, username FROM users")
for u in cur.fetchall():
    print(u)
