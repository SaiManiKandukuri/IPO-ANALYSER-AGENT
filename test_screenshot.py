import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        
        await page.get_by_role("option", name="SONASELECTION INDIA LIMITED", exact=True).click()
        await asyncio.sleep(1)
        
        await page.locator("input[value='PAN']").click(force=True)
        await asyncio.sleep(1)
        
        # Click the actual parent container if possible, or fill directly
        await page.locator("input[id='outlined-start-adornment']").fill("EGSPK5028L", timeout=3000)
        await asyncio.sleep(1)
        
        await page.screenshot(path="before_submit.png")
        
        await page.get_by_role("button", name="Submit").click(force=True)
        await asyncio.sleep(3)
        
        await page.screenshot(path="after_submit.png")
        
        await b.close()

asyncio.run(run())
