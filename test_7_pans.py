import os
import sys
import asyncio
sys.path.append('execution')
from allotment_scraper import KFintechScraper
from playwright.async_api import async_playwright

pans = [
    "EGSPK5028L",
    "ESDPR1549L",
    "EMAPK6241K",
    "HZMPP5222D",
    "DHZPA1830D",
    "DNGPK6502M",
    "Dpapk6657h"
]
pans = [p.strip().upper() for p in pans]

async def get_all_active_kfintech():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        page = await b.new_page()
        await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        await page.locator("#demo-multiple-name").click(force=True, timeout=5000)
        await asyncio.sleep(1)
        options = await page.locator("li.MuiMenuItem-root").all_inner_texts()
        active = [opt.strip() for opt in options if opt.strip()]
        await b.close()
        return active

async def run_test():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = "5911365703" # Your chat id
    
    import requests
    def send_photo(text, photo_path):
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        try:
            with open(photo_path, 'rb') as photo:
                payload = {"chat_id": chat_id, "caption": text, "parse_mode": "Markdown"}
                requests.post(url, data=payload, files={"photo": photo})
        except Exception as e:
            print(f"Error sending photo: {e}")

    print("Fetching active IPOs from KFintech...")
    
    # Clear old screenshots
    import shutil
    if os.path.exists('screenshots'):
        shutil.rmtree('screenshots')
    os.makedirs('screenshots', exist_ok=True)

    all_ipos = await get_all_active_kfintech()
    print(f"Found {len(all_ipos)} active IPOs. Starting concurrent check for 7 PANs...")
    
    scraper = KFintechScraper()
    # This will check ALL 7 PANs concurrently. Inside each PAN, it will check ALL 86 IPOs.
    results = await scraper.check_allotments_bulk(pans, all_ipos)
    
    for pan, allotments in results.items():
        if allotments:
            msg = f"🎉 *ALLOTMENT ALERT* 🎉\n\nYour PAN `{pan}` has been checked!\n\n"
            for allot in allotments:
                msg += f"🏢 *Company:* {allot['company']}\n"
                msg += f"✅ *Status:* {allot['allotted']}\n\n"
            
            if 'screenshot' in allotments[0] and allotments[0]['screenshot']:
                send_photo(msg, allotments[0]['screenshot'])
            else:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})

if __name__ == '__main__':
    asyncio.run(run_test())
