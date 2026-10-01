import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        
        async def handle_request(route, request):
            if request.method == "POST" or "api" in request.url:
                print(f"REQUEST: {request.method} {request.url}")
                if request.post_data:
                    print(f"DATA: {request.post_data}")
            await route.continue_()
            
        await page.route("**/*", handle_request)
        
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        
        await page.get_by_role("option", name="SONASELECTION INDIA LIMITED", exact=True).click()
        await asyncio.sleep(1)
        
        await page.locator("input[value='PAN']").click(force=True)
        await asyncio.sleep(1)
        
        input_loc = page.locator("input[id='outlined-start-adornment']")
        await input_loc.click()
        # Instead of fill, try typing to trigger React events
        await input_loc.type("EGSPK5028L", delay=100)
        await asyncio.sleep(1)
        
        print("Clicking submit...")
        await page.get_by_role("button", name="Submit").click(force=True)
        await asyncio.sleep(5)
        
        await b.close()

asyncio.run(run())
