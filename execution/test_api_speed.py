import requests
import time

def test_speed():
    url = "https://0uz601ms56.execute-api.ap-south-1.amazonaws.com/prod/api/query?type=pan"
    headers = {
        "accept": "application/json, text/plain, */*",
        "origin": "https://ipostatus.kfintech.com",
        "referer": "https://ipostatus.kfintech.com/",
        "client_id": "82437854510",
        "reqparam": "EGSPK5028L"
    }

    start = time.time()
    for _ in range(10):
        response = requests.get(url, headers=headers)
    end = time.time()
    
    print(f"Time for 10 requests: {end-start:.2f} seconds")
    print(f"Estimated time for 500 requests: {(end-start)*50:.2f} seconds")

test_speed()
