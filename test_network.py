import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        
        async def handle_request(route, request):
            if "amazonaws.com" in request.url:
                print(f"INTERCEPTED API REQUEST: {request.url}")
                print(f"METHOD: {request.method}")
                print(f"HEADERS: {request.headers}")
                print(f"POST DATA: {request.post_data}")
            await route.continue_()
            
        await page.route("**/*", handle_request)
        
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        
        await page.get_by_role("option", name="SONASELECTION INDIA LIMITED", exact=True).click()
        await asyncio.sleep(1)
        
        # Click the radio button forcefully
        print("Clicking PAN radio button...")
        await page.locator("input[value='pan']").click(force=True, timeout=5000)
        await asyncio.sleep(1)
        
        print("Filling PAN...")
        await page.locator("input[id='pan']").fill("EGSPK5028L", timeout=3000)
        
        print("Filling Captcha...")
        await page.locator("input[id='captcha']").fill("12345", timeout=3000)
        
        print("Clicking submit...")
        await page.locator("#btnGo").click(force=True, timeout=3000)
        await asyncio.sleep(2)
        
        await b.close()

asyncio.run(run())
