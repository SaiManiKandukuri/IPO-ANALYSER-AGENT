import requests

url = "https://0uz601ms56.execute-api.ap-south-1.amazonaws.com/prod/api/query?type=ipo"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://ipostatus.kfintech.com",
    "Referer": "https://ipostatus.kfintech.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9"
}

print("Trying GET...")
res = requests.get(url, headers=headers)
print(res.status_code)
print(res.text)

print("\nTrying POST...")
res2 = requests.post(url, headers=headers, json={})
print(res2.status_code)
print(res2.text)
