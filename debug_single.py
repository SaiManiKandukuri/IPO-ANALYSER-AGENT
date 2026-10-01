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
        
        # Test finding SONASELECTION INDIA LIMITED exact
        name = "SONASELECTION INDIA LIMITED"
        
        # Try get_by_role option
        try:
            await page.get_by_role("option", name=name, exact=True).click(timeout=3000)
            print("Successfully clicked exact name using get_by_role!")
        except Exception as e:
            print(f"Failed get_by_role: {e}")
            
        await b.close()

asyncio.run(test_kfin())
