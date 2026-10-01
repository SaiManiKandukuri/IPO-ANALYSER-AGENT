import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_chat_id TEXT PRIMARY KEY,
            pan_number TEXT,
            status TEXT DEFAULT 'PENDING'
        )
    ''')
    conn.commit()
    conn.close()

def upsert_user(chat_id, pan_number, status='PENDING'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (telegram_chat_id, pan_number, status)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_chat_id) DO UPDATE SET
            pan_number = excluded.pan_number,
            status = excluded.status
    ''', (str(chat_id), pan_number, status))
    conn.commit()
    conn.close()

def update_status(chat_id, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET status = ? WHERE telegram_chat_id = ?', (status, str(chat_id)))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def get_user(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT pan_number, status FROM users WHERE telegram_chat_id = ?', (str(chat_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"pan_number": row[0], "status": row[1]}
    return None

def get_all_users_by_status(status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT telegram_chat_id, pan_number FROM users WHERE status = ?', (status,))
    rows = cursor.fetchall()
    conn.close()
    return [{"chat_id": row[0], "pan_number": row[1]} for row in rows]

if __name__ == '__main__':
    init_db()
    print(f"Database initialized at {DB_PATH}")
