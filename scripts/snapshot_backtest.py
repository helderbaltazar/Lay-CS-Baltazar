import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playwright.sync_api import sync_playwright
import time
from integration.layback import get_cookies_from_db

def run():
    cookies = get_cookies_from_db()
    if not cookies:
        print("Sem cookies no banco.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()
        
        print("Navigating to Layback Backtest...")
        page.goto("https://backtest.layback.trade/")
        time.sleep(5) # wait for load
        page.screenshot(path="scratch/layback_backtest.png", full_page=True)
        print("Screenshot saved to scratch/layback_backtest.png")
        
        # also try layback dashboard just in case we need to navigate
        page.goto("https://bot.layback.trade/")
        time.sleep(3)
        page.screenshot(path="scratch/layback_dashboard.png")
        print("Dashboard screenshot saved")

        browser.close()

if __name__ == "__main__":
    os.makedirs("scratch", exist_ok=True)
    run()
