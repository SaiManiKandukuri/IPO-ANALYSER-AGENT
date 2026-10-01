import time
from playwright.sync_api import sync_playwright

class KFintechScraper:
    def __init__(self):
        self.url = "https://ipostatus.kfintech.com"

    def check_allotment_for_pan(self, pan_number, test_single_ipo=False):
        results = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print(f"[KFintech] Navigating to {self.url}...")
            page.goto(self.url, wait_until="networkidle")
            time.sleep(2)

            print("[KFintech] Extracting active IPOs...")
            try:
                page.locator("#demo-multiple-name").click(force=True, timeout=5000)
                time.sleep(1)
                
                options = page.locator("li.MuiMenuItem-root").all_inner_texts()
                ipo_names = [opt.strip() for opt in options if opt.strip()]
                print(f"[KFintech] Found {len(ipo_names)} active IPOs.")
                
                page.keyboard.press("Escape")
                time.sleep(1)
            except Exception as e:
                print(f"[KFintech] Error reading dropdown: {e}")
                browser.close()
                return results

            if test_single_ipo and ipo_names:
                ipo_names = [ipo_names[0]]

            for ipo_name in ipo_names:
                print(f"\n[KFintech] Checking PAN {pan_number} for IPO: {ipo_name}")
                
                # Select IPO
                page.locator("#demo-multiple-name").click(force=True, timeout=5000)
                time.sleep(0.5)
                page.locator(f"li:has-text('{ipo_name}')").click(force=True, timeout=5000)
                time.sleep(0.5)
                
                # Click PAN radio
                page.locator("input[value='pan']").click(force=True, timeout=5000)
                time.sleep(0.5)
                
                # Enter PAN - The ID of the input is 'outlined-start-adornment' in MUI usually, or we can just use the placeholder
                page.locator("input[type='text']").fill(pan_number, timeout=5000)
                time.sleep(0.5)
                
                # Click Submit
                page.locator("button:has-text('Submit')").click(force=True, timeout=5000)
                print("[KFintech] Waiting 3 seconds for result...")
                time.sleep(3)
                
                page_text = page.locator("body").inner_text()
                
                if "Record Not Found" in page_text or "No Record Found" in page_text or "Invalid" in page_text:
                    print(f"[KFintech] ❌ Result: Record Not Found for {ipo_name}.")
                else:
                    print(f"[KFintech] 🎉 Result: Allotment found for {ipo_name}!")
                        
            browser.close()
        return results

if __name__ == '__main__':
    scraper = KFintechScraper()
    print("--- Running KFintech Scraper in Test Mode (1 IPO) ---")
    scraper.check_allotment_for_pan("ABCDE1234F", test_single_ipo=True)
