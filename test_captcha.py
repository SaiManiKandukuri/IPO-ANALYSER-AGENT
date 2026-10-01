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
        
        print("Filling PAN...")
        await page.locator("input[id='pan']").fill("EGSPK5028L", timeout=3000)
        
        print("Filling CAPTCHA...")
        await page.locator("input[id='captcha']").fill("12345", timeout=3000)
        
        print("Clicking Submit...")
        await page.locator("#btnGo").click(force=True, timeout=3000)
        await asyncio.sleep(2)
        
        text = await page.locator("body").inner_text()
        print("RESULT:")
        print(text[:500])
        
        await b.close()

asyncio.run(run())
