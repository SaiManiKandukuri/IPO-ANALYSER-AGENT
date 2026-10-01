import requests
import json
import asyncio
import aiohttp

def test_fetch_ipos():
    url = "https://0uz601ms56.execute-api.ap-south-1.amazonaws.com/prod/api/query?type=ipos"
    headers = {
        "origin": "https://ipostatus.kfintech.com",
        "referer": "https://ipostatus.kfintech.com/",
    }
    resp = requests.get(url, headers=headers)
    return resp.json()

async def check_pan(ipos, pan):
    url = "https://0uz601ms56.execute-api.ap-south-1.amazonaws.com/prod/api/query?type=pan"
    headers = {
        "origin": "https://ipostatus.kfintech.com",
        "referer": "https://ipostatus.kfintech.com/",
    }
    valid = []
    
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for ipo in ipos:
            client_id = list(ipo.keys())[0]
            name = ipo[client_id]
            task = session.get(url, headers={"client_id": client_id, "reqparam": pan})
            tasks.append((client_id, name, task))
            
        for client_id, name, task in tasks:
            resp = await task
            try:
                data = await resp.json()
                err_str = str(data.get("error", "")).lower()
                if err_str and ("not found" in err_str or "invalid" in err_str or "bad req" in err_str or "unexpected" in err_str):
                    continue
                valid.append((client_id, name, data))
            except Exception as e:
                pass
    return valid

ipos = test_fetch_ipos()
print(f"Found {len(ipos)} IPOs")
valid = asyncio.run(check_pan(ipos, "EGSPK5028L"))
print(f"Valid apps for EGSPK5028L: {len(valid)}")
for v in valid:
    print(v[1])
