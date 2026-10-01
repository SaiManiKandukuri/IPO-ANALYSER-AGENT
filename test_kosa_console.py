import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        
        page.on("console", lambda msg: print(f"Browser Console [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"Page Error: {err}"))
        
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        
        await page.get_by_role("option", name="KOSAMATTAM FINANCE LIMITED - NCD36 - FEBRUARY 2026", exact=True).click(force=True)
        await asyncio.sleep(1)
        
        input_loc = page.locator("input[id='outlined-start-adornment']")
        await input_loc.fill("EGSPK5028L")
        
        page.on("response", lambda r: print("Response:", r.url, "Method:", r.request.method))
        
        async with page.expect_response(lambda r: "api/query" in r.url and "type=pan" in r.url, timeout=10000) as response_info:
            await page.get_by_role("button", name="Submit").click(force=True)
            
        resp = await response_info.value
        print("API Response JSON:", await resp.json())
        
        await asyncio.sleep(5)
        await page.screenshot(path="debug_kosa.png")
        await b.close()

asyncio.run(run())
