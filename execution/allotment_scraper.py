import json
import os
import asyncio
from datetime import datetime, timedelta, timezone
from playwright.async_api import async_playwright

def get_todays_ipos():
    """
    Returns a list of IPOs that are declaring their allotment today.
    Dates are matched against the 'Allotment_Date' field (YYYY-MM-DD) in ipo_data.json.
    """
    json_path = os.path.join(os.path.dirname(__file__), '..', 'ipo_data.json')
    if not os.path.exists(json_path):
        return []
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    today_str = ist_now.strftime('%Y-%m-%d')
    
    todays_ipos = []
    for ipo in data:
        allot_date = ipo.get('Allotment_Date', '-')
        if allot_date == today_str:
            todays_ipos.append(ipo['Company'])
            
    return todays_ipos

class KFintechScraper:
    def __init__(self):
        self.url = "https://ipostatus.kfintech.com"
        
    async def get_active_dropdown_ipos(self):
        """
        Fast, single-browser check to get all currently active IPOs on KFintech.
        Used to verify if the IPO has actually been released before running 500 PANs.
        """
        active_ipo_names = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(self.url, wait_until="networkidle")
                await page.locator("#demo-multiple-name").click(force=True, timeout=5000)
                await asyncio.sleep(1)
                options = await page.locator("li.MuiMenuItem-root").all_inner_texts()
                active_ipo_names = [opt.strip() for opt in options if opt.strip()]
            except Exception as e:
                print(f"[KFintech] Error reading active dropdown: {e}")
            finally:
                await browser.close()
        return active_ipo_names
        
    async def _check_single_pan_ipo(self, browser, pan_number, target_ipos):
        results = []
        page = await browser.new_page()
        try:
            await page.goto(self.url, wait_until="networkidle")
            await page.locator("#demo-multiple-name").click(force=True, timeout=5000)
            await asyncio.sleep(1)
            
            options = await page.locator("li.MuiMenuItem-root").all_inner_texts()
            
            # Find all matches first
            matches = []
            for target in target_ipos:
                t_simple = target.lower().replace('limited', '').replace('ltd', '').strip()
                found = False
                for active_exact in options:
                    if not active_exact.strip():
                        continue
                    a_simple = active_exact.lower().replace('limited', '').replace('ltd', '').strip()
                    if t_simple in a_simple or a_simple in t_simple:
                        matches.append((target, active_exact.strip()))
                        found = True
                        break
                if not found:
                    pass
                    # print(f"[KFintech] Could not find {target} in active dropdown.")

            # Process each match
            for target, matched_ipo_clean in matches:
                print(f"[KFintech] Checking PAN {pan_number} for {matched_ipo_clean}...")
                try:
                    await page.goto(self.url, wait_until="networkidle")
                    await page.locator("#demo-multiple-name").click(force=True, timeout=5000)
                    await asyncio.sleep(0.5)
                    
                    # Use get_by_role with exact=True for bulletproof matching
                    await page.get_by_role("option", name=matched_ipo_clean, exact=True).click(force=True, timeout=5000)
                    await asyncio.sleep(0.5)
                    
                    try:
                        await page.locator("input[value='PAN']").click(force=True, timeout=5000)
                    except: pass
                    
                    input_loc = page.locator("input[id='outlined-start-adornment']")
                    await input_loc.wait_for(state="visible", timeout=5000)
                    await input_loc.click(timeout=5000)
                    await input_loc.fill(pan_number, timeout=5000)
                    
                    try:
                        # Strictly wait for the PAN query API response!
                        async with page.expect_response(lambda r: "api/query" in r.url and "type=pan" in r.url, timeout=10000) as response_info:
                            await page.get_by_role("button", name="Submit").click(force=True, timeout=5000)
                        
                        resp = await response_info.value
                        json_data = await resp.json()
                        
                        safe_ipo_name = matched_ipo_clean.replace(" ", "_").replace("/", "")
                        screenshot_path = f"screenshots/{pan_number}_{safe_ipo_name}.png"
                        
                        # Handle Bad Request, Not Found, or Server Errors
                        err_str = str(json_data.get("error", "")).lower()
                        if err_str and ("not found" in err_str or "invalid" in err_str or "bad req" in err_str or "unexpected" in err_str):
                            print(f"[KFintech] ❌ Result: Record Not Found (or API Error) for {matched_ipo_clean}.")
                        else:
                            await asyncio.sleep(2) # Wait for React to render the table
                            await page.screenshot(path=screenshot_path)
                            
                            # Convert JSON to string to check for 0 shares easily
                            json_str = str(json_data).lower()
                            if "'allot': '0'" in json_str or '"allot": "0"' in json_str or "'alloted': '0'" in json_str:
                                print(f"[KFintech] ⚠️ Result: Applied, but Not Allotted (0 shares).")
                                results.append({
                                    "company": matched_ipo_clean,
                                    "allotted": "Not Allotted (0 Shares) 😞",
                                    "screenshot": screenshot_path
                                })
                            else:
                                print(f"[KFintech] 🎉 Result: Allotted! for {matched_ipo_clean}!")
                                results.append({
                                    "company": matched_ipo_clean,
                                    "allotted": "Allotted! 🎉",
                                    "screenshot": screenshot_path
                                })
                    except Exception as inner_e:
                        print(f"[KFintech] API/Submit Error: {inner_e}")
                        
                except Exception as e:
                    print(f"[KFintech] Error during check for {matched_ipo_clean}: {e}")
                
        except Exception as e:
            print(f"Error checking pan {pan_number}: {e}")
        finally:
            await page.close()
        return pan_number, results

    async def check_allotments_bulk(self, pans, target_ipos):
        if not target_ipos:
            return {}
            
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
            
        pan_results = {}
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            # Concurrency limit of 10 pages at a time
            sem = asyncio.Semaphore(10)
            
            async def sem_task(pan):
                async with sem:
                    return await self._check_single_pan_ipo(browser, pan, target_ipos)
                    
            tasks = [sem_task(pan) for pan in pans]
            results_tuple = await asyncio.gather(*tasks)
            
            for pan, r in results_tuple:
                pan_results[pan] = r
                
            await browser.close()
            
        return pan_results

if __name__ == '__main__':
    # Test script for KFintechScraper
    scraper = KFintechScraper()
    print("Available today:", get_todays_ipos())
    # Assuming SONASELECTION INDIA LIMITED is today for a test
    res = asyncio.run(scraper.check_allotments_bulk(["EGSPK5028L"], ["SONASELECTION"]))
    print(res)
