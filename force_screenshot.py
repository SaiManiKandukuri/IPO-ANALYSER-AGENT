import asyncio
import sys
sys.path.append('execution')
from allotment_scraper import KFintechScraper
from playwright.async_api import async_playwright

async def run_force():
    scraper = KFintechScraper()
    active = await scraper.get_active_dropdown_ipos()
    
    pan = "EGSPK5028L"
    ipo = active[0]
    
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        await page.locator("#demo-multiple-name").click(force=True)
        await asyncio.sleep(1)
        
        await page.get_by_role("option", name=ipo, exact=True).click()
        await asyncio.sleep(1)
        
        await page.locator("input[value='pan']").click()
        await page.locator("input[id='pan']").fill(pan)
        await page.locator("input[id='captcha']").fill("12345")
        
        await page.locator("#btnGo").click(force=True)
        await asyncio.sleep(2)
        
        text = await page.locator("body").inner_text()
        print("RESULT:")
        print(text[:500])
        await b.close()

if __name__ == '__main__':
    asyncio.run(run_force())
