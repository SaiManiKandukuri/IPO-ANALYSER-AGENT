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
        await asyncio.sleep(1)
        
        print("Clicking PAN radio...")
        await page.locator("input[value='PAN']").click(force=True)
        await asyncio.sleep(1)
        
        print("Filling PAN...")
        await page.locator("input[id='outlined-start-adornment']").fill("EGSPK5028L", timeout=3000)
        
        print("Clicking submit...")
        # What is the submit button ID? Let me parse it.
        # Wait, I'll use text instead or role.
        await page.get_by_role("button", name="Submit").click(force=True)
        await asyncio.sleep(2)
        
        text = await page.locator("body").inner_text()
        print("RESULT:")
        print(text[:500])
        
        await b.close()

asyncio.run(run())
