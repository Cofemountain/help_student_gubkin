import sqlite3
import sys

def migrate(db_path='oge_physics.db'):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS task_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
        user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
        author_name VARCHAR(128) NOT NULL,
        author_role VARCHAR(32) NOT NULL DEFAULT 'student',
        text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_task_comments_task_id ON task_comments(task_id);')
    con.commit()
    print("task_comments table created/verified successfully in", db_path)

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'oge_physics.db'
    migrate(path)
