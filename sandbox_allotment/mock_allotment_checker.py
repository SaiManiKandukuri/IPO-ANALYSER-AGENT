import os
import random
import requests
from sandbox_db import get_all_users

def check_allotment_mock(pan):
    """
    Simulates a registrar API call.
    Returns randomly either an allotment success or failure.
    """
    is_allotted = random.choice([True, False])
    if is_allotted:
        return {
            "status": "success",
            "applied": 35,
            "allotted": 35
        }
    else:
        return {
            "status": "failed",
            "applied": 35,
            "allotted": 0
        }

def main():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Please set TELEGRAM_BOT_TOKEN environment variable.")
        return

    users = get_all_users()
    if not users:
        print("No users registered in the database.")
        return

    print(f"Checking allotment for {len(users)} registered users...")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    for user in users:
        chat_id = user["chat_id"]
        pan = user["pan"]
        
        print(f"Checking PAN {pan}...")
        result = check_allotment_mock(pan)
        
        # Build beautifully formatted Telegram DM
        if result["status"] == "success":
            msg = f"🎉 *Allotment Successful!*\n\n"
            msg += f"🏢 *Company:* Varmora Granito (Mock)\n"
            msg += f"💳 *PAN:* `{pan}`\n"
            msg += f"📦 *Shares Applied:* {result['applied']}\n"
            msg += f"✅ *Shares Allotted:* {result['allotted']}\n\n"
            msg += f"🔗 _Verify yourself here: [KFintech Link]_"
        else:
            msg = f"😔 *Allotment Failed*\n\n"
            msg += f"🏢 *Company:* Varmora Granito (Mock)\n"
            msg += f"💳 *PAN:* `{pan}`\n"
            msg += f"📦 *Shares Applied:* {result['applied']}\n"
            msg += f"❌ *Shares Allotted:* {result['allotted']}\n\n"
            msg += f"🔗 _Verify yourself here: [KFintech Link]_"
            
        # Send Private DM
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "Markdown"
        }
        try:
            r = requests.post(url, json=payload)
            if r.status_code == 200:
                print(f"✅ Successfully sent DM to Chat ID: {chat_id}")
            else:
                print(f"❌ Failed to send DM to {chat_id}: {r.text}")
        except Exception as e:
            print(f"Error connecting to Telegram: {e}")

if __name__ == '__main__':
    main()
