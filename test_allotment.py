import os
import sys
import asyncio
import time
sys.path.append('execution')
from playwright.async_api import async_playwright

async def check_single_ipo(browser, pan_number, ipo_name, chat_id, bot_token):
    import requests
    
    def send_photo(text, photo_path):
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        try:
            with open(photo_path, 'rb') as photo:
                payload = {"chat_id": chat_id, "caption": text, "parse_mode": "Markdown"}
                requests.post(url, data=payload, files={"photo": photo})
        except Exception as e:
            print(f"Error sending photo: {e}")

    page = await browser.new_page()
    try:
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        
        await page.locator("#demo-multiple-name").click(force=True, timeout=5000)
        await asyncio.sleep(0.5)
        await page.locator(f"li:has-text('{ipo_name}')").click(force=True, timeout=5000)
        await asyncio.sleep(0.5)
        
        try: await page.locator("input[value='pan']").click(force=True, timeout=5000)
        except: pass
        
        try: await page.locator("input[type='text']").fill(pan_number, timeout=5000)
        except: pass
        
        try: await page.locator("button:has-text('Submit')").click(force=True, timeout=5000)
        except: await page.locator("button").last.click(force=True, timeout=5000)
        
        await asyncio.sleep(3)
        page_text = await page.locator("body").inner_text()
        page_text_lower = page_text.lower()
        
        safe_name = ipo_name.replace(' ', '_').replace('/', '')
        screenshot_path = f"screenshots/test_{safe_name}.png"
        await page.screenshot(path=screenshot_path)
        
        if "record not found" in page_text_lower or "no record found" in page_text_lower or "invalid" in page_text_lower or "status was not found" in page_text_lower:
            print(f"Skipping {ipo_name} - Not Applied")
        elif "0" in page_text and "Shares Allotted" in page_text:
            msg = f"🏢 *{ipo_name}*\n✅ *Status:* ⚠️ Applied, but 0 shares allotted."
            send_photo(msg, screenshot_path)
        else:
            msg = f"🏢 *{ipo_name}*\n✅ *Status:* 🎉 Yes! Allotment data found!"
            send_photo(msg, screenshot_path)
            
    except Exception as e:
        print(f"Error checking {ipo_name}: {e}")
    finally:
        await page.close()

async def run_spam_test(pan_number, chat_id):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("[KFintech] Extracting active IPOs...")
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        await page.locator("#demo-multiple-name").click(force=True, timeout=5000)
        await asyncio.sleep(1)
        options = await page.locator("li.MuiMenuItem-root").all_inner_texts()
        active_ipo_names = [opt.strip() for opt in options if opt.strip()]
        await page.close()
        
        print(f"⚠️ ASYNC SPAMMING {len(active_ipo_names)} IPOs! This will be extremely fast.")
        
        # We will use a Semaphore to limit concurrent pages to 10 to avoid crashing KFintech or our RAM
        sem = asyncio.Semaphore(10)
        
        async def sem_task(ipo):
            async with sem:
                await check_single_ipo(browser, pan_number, ipo, chat_id, bot_token)
                
        tasks = [sem_task(ipo) for ipo in active_ipo_names]
        await asyncio.gather(*tasks)
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run_spam_test("EGSPK5028L", "5911365703"))
