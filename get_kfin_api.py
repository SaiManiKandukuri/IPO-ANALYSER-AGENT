import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        
        # Intercept all requests
        requests_made = []
        page.on("request", lambda request: requests_made.append(request.url))
        
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        
        # Select IPO
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        await page.get_by_role("option", name="SONASELECTION INDIA LIMITED", exact=True).click()
        await asyncio.sleep(1)
        
        print("ALL API requests made during load:")
        for r in requests_made:
            if r.startswith("http") and not r.endswith(".css") and not r.endswith(".png") and not r.endswith(".svg"):
                print(r)
                
        await b.close()

asyncio.run(run())
