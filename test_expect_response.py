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
        input_loc = page.locator("input[id='outlined-start-adornment']")
        await input_loc.click()
        await input_loc.type("EGSPK5028L", delay=50)
        
        # Start waiting for response BEFORE clicking submit
        async with page.expect_response(lambda r: "api/query" in r.url) as response_info:
            await page.get_by_role("button", name="Submit").click(force=True)
            
        resp = await response_info.value
        json_data = await resp.json()
        print("API JSON:", json_data)
        
        await b.close()

asyncio.run(run())
