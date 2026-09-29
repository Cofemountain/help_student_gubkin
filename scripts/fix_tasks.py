import sqlite3

def run():
    con = sqlite3.connect('/var/www/oge_physics/oge_physics.db')
    cur = con.cursor()
    cur.execute("""UPDATE tasks SET 
        question='Автомобиль проехал первую половину пути со скоростью 60 км/ч, а вторую со скоростью 40 км/ч. Какова средняя скорость автомобиля на всем пути?',
        topic_id=1, grade=9, part='PART_1', status='OPEN', tutor_id=NULL 
        WHERE id=6""")
    cur.execute("""UPDATE tasks SET 
        question='Определите давление керосина на дно бака высотой 1,5 м, если бак заполнен наполовину. Плотность керосина 800 кг/м³.',
        topic_id=25, grade=7, part='PART_1', status='OPEN', tutor_id=NULL 
        WHERE id=7""")
    cur.execute("""UPDATE tasks SET 
        question='Два резистора с сопротивлениями R1 = 6 Ом и R2 = 12 Ом соединены параллельно и подключены к источнику с напряжением 24 В. Найдите общую силу тока в цепи и мощность на первом резисторе.',
        topic_id=43, grade=8, part='PART_2', status='OPEN', tutor_id=NULL 
        WHERE id=8""")
    cur.execute("UPDATE users SET active_role='tutor', base_role='tutor' WHERE telegram_id=257427576")
    con.commit()
    print("Tasks after update:")
    for r in cur.execute("SELECT id, status, student_id, tutor_id, grade, part, question FROM tasks WHERE id >= 6").fetchall():
        print(r)
    con.close()

if __name__ == '__main__':
    run()
