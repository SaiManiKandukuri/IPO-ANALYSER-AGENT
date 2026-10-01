from playwright.sync_api import sync_playwright

def intercept():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("request", lambda request: print(f">>> {request.method} {request.url}"))
        print("Navigating to KFintech...")
        page.goto("https://ipostatus.kfintech.com", wait_until="networkidle")
        print("Taking screenshot...")
        page.screenshot(path="sandbox_allotment/kfintech_screenshot.png")
        print("Done!")
        browser.close()

if __name__ == '__main__':
    intercept()
