import os
import requests
import time
from users_db import upsert_user, update_status, get_all_users_by_status, init_db

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Assumes the admin's ID is stored here

if not BOT_TOKEN:
    print("TELEGRAM_BOT_TOKEN environment variable not set.")
    exit(1)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def handle_update(update):
    message = update.get('message')
    if not message:
        return
        
    chat_id = str(message.get('chat', {}).get('id'))
    text = message.get('text', '').strip()
    
    if not text.startswith('/'):
        return

    parts = text.split()
    command = parts[0].lower()

    if command == '/register':
        if len(parts) != 2:
            send_message(chat_id, "⚠️ Invalid format. Use: `/register ABCDE1234F`")
            return
            
        pan = parts[1].upper()
        if len(pan) != 10:
            send_message(chat_id, "⚠️ Invalid PAN. Must be 10 characters.")
            return

        upsert_user(chat_id, pan, 'ACTIVE')
        
        reply_msg = (
            "🎉 *Registration Successful!*\n\n"
            f"Your PAN `{pan}` is now actively being tracked for free.\n\n"
            "You will receive an automatic message here whenever a new IPO allotment is announced!"
        )
        send_message(chat_id, reply_msg)
        
        # Notify Admin
        if ADMIN_CHAT_ID:
            admin_msg = f"🔔 *New Registration!*\nUser `{chat_id}` wants to track PAN `{pan}`."
            send_message(ADMIN_CHAT_ID, admin_msg)

    elif command == '/approve':
        if chat_id != str(ADMIN_CHAT_ID):
            send_message(chat_id, "⛔️ Unauthorized.")
            return
            
        if len(parts) != 2:
            send_message(chat_id, "Use: `/approve <chat_id>`")
            return
            
        target_id = parts[1]
        if update_status(target_id, 'ACTIVE'):
            send_message(chat_id, f"✅ Approved user {target_id}.")
            send_message(target_id, "🎉 *Your subscription is ACTIVE!*\n\nWe will now automatically track your IPO allotments.")
        else:
            send_message(chat_id, f"❌ Failed. User {target_id} not found.")
            
    elif command == '/reject':
        if chat_id != str(ADMIN_CHAT_ID):
            send_message(chat_id, "⛔️ Unauthorized.")
            return
            
        if len(parts) != 2:
            send_message(chat_id, "Use: `/reject <chat_id>`")
            return
            
        target_id = parts[1]
        if update_status(target_id, 'REJECTED'):
            send_message(chat_id, f"✅ Rejected user {target_id}.")
            send_message(target_id, "❌ Your registration was rejected. Please contact support.")
        else:
            send_message(chat_id, f"❌ Failed. User {target_id} not found.")

    elif command == '/pending':
        if chat_id != str(ADMIN_CHAT_ID):
            send_message(chat_id, "⛔️ Unauthorized.")
            return
            
        pending_users = get_all_users_by_status('PENDING')
        if not pending_users:
            send_message(chat_id, "No pending users.")
            return
            
        msg = "📋 *Pending Users:*\n"
        for u in pending_users:
            msg += f"• `{u['chat_id']}` (PAN: {u['pan_number']})\n"
        send_message(chat_id, msg)
        
    elif command == '/start':
        welcome_msg = (
            "👋 Welcome to IPO Analyser!\n\n"
            "We provide automated KFintech Allotment Tracking directly to your DMs.\n\n"
            "To get started, register your PAN by sending:\n"
            "`/register ABCDE1234F`"
        )
        send_message(chat_id, welcome_msg)

def poll_telegram():
    print("Starting Telegram polling bot for Subscriptions...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    last_update_id = 0

    while True:
        try:
            params = {"offset": last_update_id + 1, "timeout": 30}
            response = requests.get(url, params=params, timeout=35)
            data = response.json()
            
            if not data.get("ok"):
                print(f"Error from Telegram API: {data}")
                time.sleep(5)
                continue

            for update in data.get("result", []):
                last_update_id = update["update_id"]
                handle_update(update)

        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    init_db()
    poll_telegram()
