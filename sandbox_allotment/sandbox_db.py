import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sandbox_users.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_chat_id TEXT PRIMARY KEY,
            pan_number TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_or_update_user(chat_id, pan_number):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (telegram_chat_id, pan_number)
        VALUES (?, ?)
        ON CONFLICT(telegram_chat_id) 
        DO UPDATE SET pan_number=excluded.pan_number
    ''', (str(chat_id), pan_number.upper()))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT telegram_chat_id, pan_number FROM users')
    rows = c.fetchall()
    conn.close()
    return [{"chat_id": row[0], "pan": row[1]} for row in rows]

if __name__ == '__main__':
    init_db()
    print(f"Database initialized at {DB_PATH}")
