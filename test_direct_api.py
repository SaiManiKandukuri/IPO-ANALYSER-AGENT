import requests

url = "https://0uz601ms56.execute-api.ap-south-1.amazonaws.com/prod/api/query?type=pan"
headers = {
    "accept": "application/json, text/plain, */*",
    "origin": "https://ipostatus.kfintech.com",
    "referer": "https://ipostatus.kfintech.com/",
    "client_id": "82437854510",
    "reqparam": "EGSPK5028L"
}

response = requests.get(url, headers=headers)
print("STATUS CODE:", response.status_code)
print("RESPONSE TEXT:", response.text)
