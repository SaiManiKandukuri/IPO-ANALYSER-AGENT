import requests
import json

url = "https://0uz601ms56.execute-api.ap-south-1.amazonaws.com/prod/api/query?type=pan"
headers = {
    "accept": "application/json, text/plain, */*",
    "origin": "https://ipostatus.kfintech.com",
    "referer": "https://ipostatus.kfintech.com/",
    "client_id": "82437854510",
    "reqparam": "EGSPK5028L"
}

try:
    response = requests.get(url, headers=headers)
    print("Status:", response.status_code)
    try:
        print("JSON:", json.dumps(response.json(), indent=2))
    except:
        print("Text:", response.text)
except Exception as e:
    print(e)
