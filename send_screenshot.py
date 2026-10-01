import requests
import os

bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = "5911365703"

url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
with open("kfin_state.png", "rb") as photo:
    payload = {"chat_id": chat_id, "caption": "Hey! Here is what the KFintech bot sees when it tries to fill the PAN."}
    res = requests.post(url, data=payload, files={"photo": photo})
    print(res.json())
