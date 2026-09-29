import sqlite3

def migrate(db_path='oge_physics.db'):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cols = [col[1] for col in cur.execute('PRAGMA table_info(tasks)').fetchall()]
    
    if 'request_type' not in cols:
        cur.execute("ALTER TABLE tasks ADD COLUMN request_type VARCHAR(32) DEFAULT 'TASK'")
        print("Added request_type")
        
    if 'telemost_url' not in cols:
        cur.execute("ALTER TABLE tasks ADD COLUMN telemost_url VARCHAR(256) DEFAULT ''")
        print("Added telemost_url")
        
    if 'teacher_response' not in cols:
        cur.execute("ALTER TABLE tasks ADD COLUMN teacher_response TEXT DEFAULT ''")
        print("Added teacher_response")
        
    if 'solution_photo_url' not in cols:
        cur.execute("ALTER TABLE tasks ADD COLUMN solution_photo_url TEXT DEFAULT ''")
        print("Added solution_photo_url")

    if 'student_clarification' not in cols:
        cur.execute("ALTER TABLE tasks ADD COLUMN student_clarification TEXT DEFAULT ''")
        print("Added student_clarification")

    hw_cols = [col[1] for col in cur.execute('PRAGMA table_info(homeworks)').fetchall()]
    if 'bank_task_id' not in hw_cols:
        cur.execute("ALTER TABLE homeworks ADD COLUMN bank_task_id INTEGER")
        print("Added bank_task_id to homeworks")
        
    con.commit()
    print("Migration finished. Columns:", [col[1] for col in cur.execute('PRAGMA table_info(tasks)').fetchall()])

if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else 'oge_physics.db'
    migrate(path)
