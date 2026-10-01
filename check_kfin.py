import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        html = await page.content()
        with open("kfin_html.txt", "w") as f:
            f.write(html)
        await b.close()

asyncio.run(run())
