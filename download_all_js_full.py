import requests
import os
from bs4 import BeautifulSoup
import urllib.parse
from playwright.sync_api import sync_playwright
import config

os.makedirs('logs/js_chunks', exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
    with page.expect_navigation():
        page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    page.wait_for_selector("[href='/dashboard']", timeout=30000)
    
    cookies = context.cookies()
    session = requests.Session()
    for c in cookies:
        session.cookies.set(c['name'], c['value'], domain=c['domain'])
        
    r = session.get("https://bot-betfair.layback.trade/bots/150")
    html = r.text
    
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script', src=True)
    
    js_urls = [urllib.parse.urljoin("https://bot-betfair.layback.trade", s['src']) for s in scripts]
    
    for i, url in enumerate(js_urls):
        try:
            js_res = session.get(url, timeout=10)
            with open(f"logs/js_chunks/chunk_{i}.js", "w") as f:
                f.write(js_res.text)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            
    print(f"Saved {len(js_urls)} files.")
    browser.close()
