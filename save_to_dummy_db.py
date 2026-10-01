import sqlite3
import os
import glob
from datetime import datetime

def main():
    db_path = 'dummy_allotments.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS review_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pan_number TEXT,
        ipo_name TEXT,
        screenshot_path TEXT,
        status TEXT,
        created_at TEXT
    )
    ''')
    
    screenshots = glob.glob('screenshots/*.png')
    
    for s_path in screenshots:
        filename = os.path.basename(s_path)
        # DHZPA1830D_RENTOMOJO_LIMITED.png
        parts = filename.replace('.png', '').split('_', 1)
        if len(parts) == 2:
            pan, ipo = parts
            ipo = ipo.replace('_', ' ')
            
            # Check if already exists to avoid duplicates
            cursor.execute('SELECT id FROM review_queue WHERE pan_number = ? AND ipo_name = ?', (pan, ipo))
            if not cursor.fetchone():
                cursor.execute('''
                INSERT INTO review_queue (pan_number, ipo_name, screenshot_path, status, created_at)
                VALUES (?, ?, ?, 'PENDING_REVIEW', ?)
                ''', (pan, ipo, s_path, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                
    conn.commit()
    
    cursor.execute('SELECT COUNT(*) FROM review_queue')
    count = cursor.fetchone()[0]
    print(f"Stored {count} screenshots in dummy database for review.")
    
    conn.close()

if __name__ == '__main__':
    main()
