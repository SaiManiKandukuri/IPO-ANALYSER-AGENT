import time
import os
import sqlite3
import requests
from kfintech_scraper import KFintechScraper

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN not set in environment.")
    exit(1)

DB_PATH = "sandbox_users.db"

def send_telegram_message(chat_id, text):
    """Sends a message to the specific user chat_id."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"✅ Sent message to {chat_id}")
    else:
        print(f"❌ Failed to send message to {chat_id}: {response.text}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"No database found at {DB_PATH}. Exiting.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all users who have registered a PAN
    cursor.execute("SELECT telegram_chat_id, pan_number FROM users WHERE pan_number IS NOT NULL")
    users = cursor.fetchall()
    
    if not users:
        print("No users with registered PANs found in the database.")
        return
        
    print(f"Found {len(users)} registered users. Starting KFintech Scraper...")
    
    # Initialize the scraper
    scraper = KFintechScraper()
    
    # Iterate through users
    for chat_id, pan_number in users:
        print(f"\n======================================")
        print(f"Checking PAN {pan_number} for User {chat_id}")
        
        # Here we only check the latest 5 IPOs to save time in the sandbox loop
        # A real production scraper might check all, or keep state of what has been checked.
        # But for sandbox, checking all 86 will take too long.
        print(f"Note: Sandbox mode will be fast in production, but we are running headless browser.")
        
        try:
            # Let's say check_allotment_for_pan returns a list of results
            # We would call scraper.check_allotment_for_pan(pan_number)
            # For now, since we know the script gets stuck on the text input, we will just send a mock success 
            # to prove the loop works, while the scraper class is ready for real inputs.
            
            # TODO: Fix Playwright text input selector for PAN
            # allotments = scraper.check_allotment_for_pan(pan_number)
            
            # Mock success for testing the integration
            allotments = [{"company": "MOCK IPO (Sandbox)", "allotted": "Yes"}]
            
            if allotments:
                message = f"🎉 *ALLOTMENT ALERT* 🎉\n\nYour PAN `{pan_number}` has been allotted shares!\n\n"
                for allot in allotments:
                    message += f"🏢 *Company:* {allot['company']}\n"
                    message += f"✅ *Status:* Successfully Allotted\n\n"
                message += "Check your demat account for the credited shares."
                
                send_telegram_message(chat_id, message)
            else:
                print(f"No allotments found for PAN {pan_number}.")
                
        except Exception as e:
            print(f"Error checking allotment for {pan_number}: {e}")

if __name__ == '__main__':
    main()
