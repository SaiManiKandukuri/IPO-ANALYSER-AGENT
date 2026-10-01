import os
import re
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from user_db import init_db, register_user
import historical_check

# Load environment variables from .env file (one directory up since this is in execution/)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Welcome to the IPO Analyser Bot! 🚀\n\n"
        "Please register your PAN number by sending it to me.\n"
        "Example: `ABCDE1234F`"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    chat_id = str(update.message.chat_id)

    # Basic PAN Validation (5 letters, 4 numbers, 1 letter)
    if re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', text):
        register_user(chat_id, text)
        msg = await update.message.reply_text(
            "✅ Registered successfully!\n\n"
            "Presently only KFin registrar is available. In the upcoming days, we will add more registrars.\n\n"
            f"I am now spinning up a secure background task to scan for all past KFintech applications for PAN: `{text}`."
        )
        
        # Trigger historical check in background, passing the message_id so it can edit it live!
        asyncio.create_task(historical_check.run_historical_check(chat_id, text, msg.message_id))
        
    else:
        await update.message.reply_text("❌ Invalid PAN format. Please send a valid 10-character PAN (e.g., ABCDE1234F).")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    chat_id = update.effective_chat.id
    
    if data.startswith("send_all_") or data.startswith("send_allotted_"):
        pan = data.split("_")[-1]
        only_allotted = "allotted" in data
        
        await query.edit_message_text(text="📤 Uploading your screenshots...")
        
        # Find screenshots in folder
        screenshots = []
        for file in os.listdir("screenshots"):
            if file.startswith(pan):
                # Note: Currently we just send all found for this PAN. 
                # (To fully support "only_allotted", we would parse the filename or DB, 
                # but for now we'll upload them as proof of concept)
                screenshots.append(os.path.join("screenshots", file))
                
        for path in screenshots:
            await context.bot.send_photo(chat_id=chat_id, photo=open(path, 'rb'))
            
        await context.bot.send_message(chat_id=chat_id, 
                                       text="Yeah, that's all for now! We will intimate you with new allotments.")

def main():
    init_db()
    if not TELEGRAM_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN environment variable not set.")
        return
        
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is listening 24/7...")
    application.run_polling()

if __name__ == "__main__":
    main()
