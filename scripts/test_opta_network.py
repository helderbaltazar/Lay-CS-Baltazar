from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.on("response", lambda response: print(f"{response.url} - {response.status}") if "json" in response.url or "csv" in response.url or "api" in response.url else None)
    
    page.goto("https://dataviz.theanalyst.com/opta-power-rankings/")
    page.wait_for_timeout(5000)
    browser.close()
