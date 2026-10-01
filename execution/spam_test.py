import os
import sys
import time
import requests
from allotment_scraper import KFintechScraper
from playwright.sync_api import sync_playwright

bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = "5911365703"

def send_photo(chat_id, text, photo_path):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            payload = {"chat_id": chat_id, "caption": text, "parse_mode": "Markdown"}
            r = requests.post(url, data=payload, files={"photo": photo})
            print(f"Telegram API status: {r.status_code}")
    except Exception as e:
        print(f"Error sending photo: {e}")

def check_all_86_ipos(pan_number):
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")

    url = "https://ipostatus.kfintech.com"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"[KFintech] Navigating to {url}...")
        page.goto(url, wait_until="networkidle")
        time.sleep(2)

        print("[KFintech] Extracting active IPOs...")
        try:
            page.locator("#demo-multiple-name").click(force=True, timeout=5000)
            time.sleep(1)
            
            options = page.locator("li.MuiMenuItem-root").all_inner_texts()
            active_ipo_names = [opt.strip() for opt in options if opt.strip()]
            print(f"[KFintech] Found {len(active_ipo_names)} active IPOs.")
            
            page.keyboard.press("Escape")
            time.sleep(1)
        except Exception as e:
            print(f"[KFintech] Error reading dropdown: {e}")
            browser.close()
            return

        print("⚠️ WARNING: SPAMMING ALL 86 IPOS TO TELEGRAM!")
        for idx, ipo_name in enumerate(active_ipo_names):
            print(f"\n[{idx+1}/{len(active_ipo_names)}] Checking PAN {pan_number} for IPO: {ipo_name}")
            
            try:
                page.locator("#demo-multiple-name").click(force=True, timeout=5000)
                time.sleep(0.5)
                page.locator(f"li:has-text('{ipo_name}')").click(force=True, timeout=5000)
                time.sleep(0.5)
                
                try:
                    page.locator("input[value='pan']").click(force=True, timeout=5000)
                except:
                    pass
                time.sleep(0.5)
                
                try:
                    page.locator("input[type='text']").fill(pan_number, timeout=5000)
                except:
                    pass
                time.sleep(0.5)
                
                try:
                    page.locator("button:has-text('Submit')").click(force=True, timeout=5000)
                except:
                    page.locator("button").last.click(force=True, timeout=5000)
                    
                time.sleep(3)
                
                page_text = page.locator("body").inner_text()
                screenshot_path = f"screenshots/ipo_{idx}.png"
                page.screenshot(path=screenshot_path)
                
                if "Record Not Found" in page_text or "No Record Found" in page_text or "Invalid" in page_text:
                    status = "❌ Record Not Found"
                else:
                    if "0" in page_text and "Shares Allotted" in page_text:
                         status = "⚠️ Applied, but 0 shares allotted."
                    else:
                         status = "🎉 Yes! Allotment found!"
                
                msg = f"🏢 *{ipo_name}*\n✅ *Status:* {status}"
                send_photo(chat_id, msg, screenshot_path)
                
                time.sleep(2) # Anti-rate limit
                
            except Exception as e:
                print(f"Error checking {ipo_name}: {e}")
                continue
                
        browser.close()

if __name__ == '__main__':
    check_all_86_ipos("EGSPK5028L")
