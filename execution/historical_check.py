import asyncio
import aiohttp
import os
import shutil
from playwright.async_api import async_playwright
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def extract_active_ipos(page):
    await page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
    await page.locator("#demo-multiple-name").click(force=True)
    await asyncio.sleep(1)
    
    options = await page.locator("ul[role='listbox'] li").all()
    ipos = []
    for option in options:
        name = await option.text_content()
        client_id = await option.get_attribute("data-value")
        if name and client_id:
            ipos.append({"name": name.strip(), "client_id": client_id})
    return ipos

async def check_pan_fast(ipos, pan):
    url = "https://0uz601ms56.execute-api.ap-south-1.amazonaws.com/prod/api/query?type=pan"
    headers = {
        "origin": "https://ipostatus.kfintech.com",
        "referer": "https://ipostatus.kfintech.com/",
    }
    valid_apps = []
    
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for ipo in ipos:
            task = session.get(url, headers={"client_id": ipo["client_id"], "reqparam": pan}, ssl=False)
            tasks.append((ipo, task))
            
        for ipo, task in tasks:
            try:
                resp = await task
                data = await resp.json()
                err_str = str(data.get("error", "")).lower()
                
                # If error is present, skip
                if err_str and ("not found" in err_str or "invalid" in err_str or "bad req" in err_str or "unexpected" in err_str):
                    continue
                
                # Valid application found!
                # Check if it's actually allotted or not
                is_allotted = False
                if "shares" in str(data).lower() or "allotted" in str(data).lower():
                    is_allotted = True
                
                valid_apps.append({"ipo": ipo, "data": data, "is_allotted": is_allotted})
            except Exception as e:
                pass
    return valid_apps

async def capture_screenshot(page, ipo_name, pan, screenshot_path):
    # Select the IPO again
    await page.locator("#demo-multiple-name").click(force=True)
    await asyncio.sleep(0.5)
    await page.get_by_role("option", name=ipo_name, exact=True).click(force=True)
    await asyncio.sleep(0.5)
    
    # Fill PAN and submit
    input_loc = page.locator("input[id='outlined-start-adornment']")
    await input_loc.fill(pan)
    
    async with page.expect_response(lambda r: "api/query" in r.url and "type=pan" in r.url and r.request.method == "GET", timeout=10000) as response_info:
        await page.get_by_role("button", name="Submit").click(force=True)
    
    await response_info.value
    await asyncio.sleep(2) # Wait for React table
    await page.screenshot(path=screenshot_path)
    
    # Reset for next
    await page.reload(wait_until="networkidle")

async def run_historical_check(chat_id, pan, status_message_id):
    bot = Bot(token=TELEGRAM_TOKEN)
    
    # Create screenshots directory
    os.makedirs("screenshots", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, 
                                    text=f"🔍 Booting up scraping engine for PAN: `{pan}`...")
        
        # 1. Fetch active IPOs
        ipos = await extract_active_ipos(page)
        
        await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, 
                                    text=f"🔍 Scanning KFintech API for {len(ipos)} past IPOs...")
        
        # 2. Fast API Scan
        valid_apps = await check_pan_fast(ipos, pan)
        allotted = [app for app in valid_apps if app["is_allotted"]]
        
        if not valid_apps:
            await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, 
                                        text=f"✅ Scan Complete! I didn't find any past applications for `{pan}` on KFintech.")
            await browser.close()
            return
            
        await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, 
                                    text=f"📸 Found {len(valid_apps)} applications! Taking official screenshots...")
        
        # 3. Capture Screenshots
        saved_files = []
        for i, app in enumerate(valid_apps):
            safe_name = app['ipo']['name'].replace(" ", "_").replace("/", "")
            path = f"screenshots/{pan}_{safe_name}.png"
            await capture_screenshot(page, app['ipo']['name'], pan, path)
            saved_files.append(path)
            
            # Live progress
            await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, 
                                        text=f"📸 Taking screenshots... ({i+1}/{len(valid_apps)})")
            
        await browser.close()
        
        # 4. Final Summary with Buttons
        summary_text = (
            f"✅ **Scan Complete for {pan}!**\n\n"
            f"📊 Total Applications Found: {len(valid_apps)}\n"
            f"🎉 Allotted: {len(allotted)}\n"
            f"❌ Not Allotted: {len(valid_apps) - len(allotted)}\n\n"
            f"Click below to receive your official KFintech screenshots."
        )
        
        keyboard = [
            [InlineKeyboardButton("📸 Send All Screenshots", callback_data=f"send_all_{pan}")],
        ]
        if allotted:
            keyboard.append([InlineKeyboardButton(f"🎉 Send Only Allotted ({len(allotted)})", callback_data=f"send_allotted_{pan}")])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.edit_message_text(chat_id=chat_id, message_id=status_message_id, 
                                    text=summary_text, reply_markup=reply_markup, parse_mode="Markdown")

if __name__ == "__main__":
    # Test script standalone
    import sys
    if len(sys.argv) > 2:
        asyncio.run(run_historical_check(sys.argv[1], sys.argv[2], 0))
