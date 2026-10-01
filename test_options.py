import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        
        await page.get_by_role("option", name="AXIOM GAS ENGINEERING LIMITED", exact=True).click(force=True)
        await asyncio.sleep(1)
        
        input_loc = page.locator("input[id='outlined-start-adornment']")
        await input_loc.fill("EGSPK5028L")
        
        # Listen to all responses
        page.on("response", lambda r: print("Response:", r.url, "Method:", r.request.method))
        
        await page.get_by_role("button", name="Submit").click(force=True)
        await asyncio.sleep(3)
        await b.close()

asyncio.run(run())
