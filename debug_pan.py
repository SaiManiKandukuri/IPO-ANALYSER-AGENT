import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        await page.locator("li.MuiMenuItem-root").first.click(force=True)
        await asyncio.sleep(1)
        html = await page.content()
        with open("kfin_current.html", "w") as f:
            f.write(html)
        await b.close()

asyncio.run(run())
