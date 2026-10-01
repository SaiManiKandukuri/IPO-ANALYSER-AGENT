import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        
        options = await page.locator("ul[role='listbox'] li").all()
        for option in options:
            name = await option.text_content()
            value = await option.get_attribute("data-value")
            print(f"Name: {name}, ID: {value}")
            
        await b.close()

asyncio.run(run())
