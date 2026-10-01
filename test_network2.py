import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        
        page.on("request", lambda r: print("Request:", r.url))
        
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        print("--- Loaded ---")
        
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        
        print("--- Clicking IPO ---")
        await page.get_by_role("option", name="AXIOM GAS ENGINEERING LIMITED", exact=True).click(force=True)
        await asyncio.sleep(2)
        
        print("--- Done ---")
        await b.close()

asyncio.run(run())
