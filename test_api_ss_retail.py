import requests

url = "https://0uz601ms56.execute-api.ap-south-1.amazonaws.com/prod/api/query?type=pan"
headers = {
    "accept": "application/json, text/plain, */*",
    "origin": "https://ipostatus.kfintech.com",
    "referer": "https://ipostatus.kfintech.com/",
    # We need the client_id for SS RETAIL LIMITED. Let's assume it's one of them, but we don't know it.
}

