from playwright.sync_api import sync_playwright
import time

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Fetching GMP page...")
        page.goto('https://www.investorgain.com/report/ipo-gmp-live/331/')
        page.wait_for_selector('table tbody tr')
        
        rows = page.locator('table tbody tr').all()
        print(f"Found {len(rows)} GMP rows")
        if rows:
            print("Row 1:", rows[0].inner_text().split('\n'))
            
        print("Fetching Sub page...")
        page.goto('https://www.investorgain.com/report/ipo-subscription-live/333/all/')
        page.wait_for_selector('table tbody tr')
        
        rows = page.locator('table tbody tr').all()
        print(f"Found {len(rows)} Sub rows")
        if rows:
            print("Row 1:", rows[0].inner_text().split('\n'))
            
        browser.close()

if __name__ == '__main__':
    main()
