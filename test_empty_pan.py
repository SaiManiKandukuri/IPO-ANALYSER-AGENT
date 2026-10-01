import requests

url = "https://0uz601ms56.execute-api.ap-south-1.amazonaws.com/prod/api/query?type=pan"
headers = {
    "accept": "application/json, text/plain, */*",
    "origin": "https://ipostatus.kfintech.com",
    "referer": "https://ipostatus.kfintech.com/",
    "client_id": "82437854510",
    "reqparam": ""
}

try:
    response = requests.get(url, headers=headers)
    print(response.status_code)
    print(response.text)
except Exception as e:
    print(e)
