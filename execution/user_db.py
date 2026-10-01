import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_chat_id TEXT PRIMARY KEY,
            pan_number TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE'
        )
    ''')
    conn.commit()
    conn.close()

def register_user(chat_id: str, pan_number: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (telegram_chat_id, pan_number)
        VALUES (?, ?)
        ON CONFLICT(telegram_chat_id) DO UPDATE SET pan_number=excluded.pan_number
    ''', (chat_id, pan_number.upper()))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id, pan_number FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

if __name__ == "__main__":
    init_db()
    print("Database initialized at", DB_PATH)
