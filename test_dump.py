import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        
        print("Clicking dropdown...")
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        
        print("Selecting SONASELECTION...")
        await page.get_by_role("option", name="SONASELECTION INDIA LIMITED", exact=True).click()
        await asyncio.sleep(2)
        
        html = await page.content()
        with open("kfin_state.html", "w") as f:
            f.write(html)
        
        await b.close()

asyncio.run(run())
