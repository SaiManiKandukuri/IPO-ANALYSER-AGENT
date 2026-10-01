import requests

bot_token = "8913401569:AAGR8b2i66Xf7T86a0C1X9TstkO-J7yN7G8"
chat_id = "5911365703"
text = "Debug test message"

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
print("Sending request...")
response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
