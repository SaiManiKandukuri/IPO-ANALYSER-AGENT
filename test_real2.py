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
        
        await page.locator("input[id='outlined-start-adornment']").fill("EGSPK5028L", timeout=3000)
        
        await page.get_by_role("button", name="Submit").click(force=True)
        await asyncio.sleep(3)
        
        # Dump the innerHTML of the root element
        html = await page.locator("#root").inner_html()
        with open("after_submit.html", "w") as f:
            f.write(html)
            
        await b.close()

asyncio.run(run())
