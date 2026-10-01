import os
import time
import requests
import re
from sandbox_db import init_db, add_or_update_user

def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Please set TELEGRAM_BOT_TOKEN environment variable.")
        return

    print("Initializing Database...")
    init_db()

    print("Starting Telegram Registration Bot (Sandbox)...")
    url = f"https://api.telegram.org/bot{bot_token}/"
    offset = 0

    while True:
        try:
            # Poll for new messages
            res = requests.get(url + "getUpdates", params={"offset": offset, "timeout": 30}).json()
            if not res.get("ok"):
                print("Error getting updates:", res)
                time.sleep(5)
                continue
                
            updates = res.get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"].strip()
                    
                    if text.startswith("/start"):
                        msg = "🌟 *Welcome to Premium Allotment Alerts!*\n\nTo register, please send your 10-digit PAN Card Number starting with `/register `.\n\nExample: `/register ABCDE1234F`"
                        requests.post(url + "sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
                        
                    elif text.startswith("/register"):
                        parts = text.split(maxsplit=1)
                        if len(parts) > 1:
                            pan = parts[1].strip().upper()
                            # Basic PAN Regex validation
                            if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan):
                                add_or_update_user(chat_id, pan)
                                msg = f"✅ Success! Your PAN `{pan}` has been securely registered.\n\nYou will automatically receive a private alert the moment allotment results are released!"
                            else:
                                msg = "❌ Invalid PAN format. Please ensure it is a valid 10-digit PAN (e.g., ABCDE1234F)."
                        else:
                            msg = "❌ Please provide your PAN. Example: `/register ABCDE1234F`"
                            
                        requests.post(url + "sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})

            time.sleep(1)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()
