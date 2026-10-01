import asyncio
import aiohttp

async def check():
    url = "https://0uz601ms56.execute-api.ap-south-1.amazonaws.com/prod/api/query?type=pan"
    headers = {
        "origin": "https://ipostatus.kfintech.com",
        "referer": "https://ipostatus.kfintech.com/",
        "client_id": "20422755930", # KOSAMATTAM FINANCE LIMITED - NCD36
        "reqparam": "EGSPK5028L"
    }
    async with aiohttp.ClientSession() as session:
        resp = await session.get(url, headers=headers)
        print("Status:", resp.status)
        try:
            print(await resp.json())
        except:
            print(await resp.text())

asyncio.run(check())
