from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.google.com/search?q=Opta+Power+Rankings+analyst")
    page.wait_for_selector("a h3")
    first_link = page.locator("a h3").first.locator("..").get_attribute("href")
    print(f"First link: {first_link}")
    
    if first_link:
        page.goto(first_link)
        page.wait_for_timeout(3000)
        title = page.title()
        print(f"Title: {title}")
        
    browser.close()
