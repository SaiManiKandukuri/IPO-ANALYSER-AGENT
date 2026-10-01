import asyncio
import sys
from playwright.async_api import async_playwright

async def test_kfin():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        
        await page.get_by_role("option", name="SONASELECTION INDIA LIMITED", exact=True).click()
        await asyncio.sleep(1)
        
        await page.locator("input[value='pan']").click()
        await page.locator("input[id='pan']").fill("EGSPK5028L")
        
        # Look for captcha element
        if await page.locator("input[id='txtcaptcha']").count() > 0:
            print("CAPTCHA INPUT FOUND!")
        else:
            print("NO CAPTCHA INPUT FOUND!")
            
        await page.locator("a#btnGo").click(force=True)
        await asyncio.sleep(2)
        
        print("--- PAGE TEXT AFTER SUBMIT ---")
        text = await page.locator("body").inner_text()
        print(text[:1000]) # Print first 1000 chars
        print("--- END PAGE TEXT ---")
            
        await b.close()

asyncio.run(test_kfin())
