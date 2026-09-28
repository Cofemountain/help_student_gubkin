import sqlite3

con = sqlite3.connect('/var/www/oge_physics/oge_physics.db')
cur = con.cursor()
cur.execute("SELECT id, grade, block, title FROM topics ORDER BY grade, id")
topics = cur.fetchall()
print(f"Total topics: {len(topics)}")
for t in topics:
    if any(k in t[3].lower() for k in ['сосуд', 'давлен', 'ом', 'прямолинейн', 'скорост', 'рычаг', 'последовательн']):
        print(f"ID={t[0]} | Gr={t[1]} | Blk={t[2]} | {t[3]}")
