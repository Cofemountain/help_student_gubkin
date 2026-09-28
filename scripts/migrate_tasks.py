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
        
    con.commit()
    print("Migration finished. Columns:", [col[1] for col in cur.execute('PRAGMA table_info(tasks)').fetchall()])

if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else 'oge_physics.db'
    migrate(path)
