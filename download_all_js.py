import config
import requests
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import urllib.parse

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    # Login
    page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
    with page.expect_navigation():
        page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    page.wait_for_selector("[href='/dashboard'], [href*='/bots']", timeout=30000)
    page.wait_for_timeout(3000)
    
    cookies = context.cookies()
    session = requests.Session()
    for c in cookies:
        session.cookies.set(c['name'], c['value'], domain=c['domain'])
        
    r = session.get("https://bot-betfair.layback.trade/bots/150")
    html = r.text
    
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script', src=True)
    
    js_urls = [urllib.parse.urljoin("https://bot-betfair.layback.trade", s['src']) for s in scripts]
    print(f"Encontrados {len(js_urls)} scripts na pagina HTML.")
    
    bot_api_list = set()
    
    for url in js_urls:
        try:
            js_res = session.get(url, timeout=10)
            content = js_res.text
            
            # extract all strings that look like api endpoints
            api_matches = re.findall(r'/api/[a-zA-Z0-9/\-\_]+', content)
            unique_apis = set(api_matches)
            
            for a in unique_apis:
                if "bot" in a.lower() or "team" in a.lower():
                    bot_api_list.add(a)
                    
            if "api/bots" in content:
                print(f"  -> api/bots found in {url.split('/')[-1]}")
                # Exibe um pouco do contexto se tiver "team" perto
                if "team" in content.lower():
                    idx = content.find("api/bots")
                    print(f"     Context: {content[max(0, idx-50):idx+150]}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            
    print(f"\nAll related APIs found: {sorted(list(bot_api_list))}")
    
    browser.close()
