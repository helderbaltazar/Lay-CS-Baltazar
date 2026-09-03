import config
import sys
from playwright.sync_api import sync_playwright

def p(msg):
    print(msg)
    sys.stdout.flush()

bot_ids = {"0-1": 150, "0-2": 151, "0-3": 152}

with sync_playwright() as play:
    browser = play.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    )
    page = context.new_page()
    
    p("Going to login...")
    page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
    page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    
    page.wait_for_selector("text='Dashboard'", timeout=30000)
    
    for target, bot_id in bot_ids.items():
        json_file = f"data/bot_lay_{target.replace('-', '_')}.json"
        p(f"\\n--- Bot {bot_id} ---")
        
        page.click("text='Bots'")
        page.wait_for_timeout(2000)
        page.click(f"a[href='/bots/{bot_id}']")
        
        page.wait_for_selector("button:has-text('Configuração')", timeout=30000)
        page.wait_for_timeout(2000)
        page.click("button:has-text('Configuração')")
        page.wait_for_timeout(3000)
        
        p("Scrolling down iteratively...")
        # Scroll down completely so all lazy-loaded cards appear!
        for _ in range(10):
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(500)
            
        page.wait_for_timeout(2000)
        
        p("Unhiding buttons...")
        page.evaluate("""() => {
            document.querySelectorAll("div").forEach(div => {
                if (div.className && div.className.includes("[&_button]:hidden")) {
                    div.className = div.className.replace("[&_button]:hidden", "");
                }
            });
        }""")
        page.wait_for_timeout(1000)
        
        p("Clicking Editar via React...")
        page.evaluate("""() => {
            const sections = document.querySelectorAll("div.rounded-xl");
            for (let sec of sections) {
                if (sec.textContent.includes("Times para apostar") || sec.textContent.includes("Times para NÃO apostar")) {
                    const btn = Array.from(sec.querySelectorAll("button")).find(b => b.textContent.includes("Editar"));
                    if (btn) {
                        const reactPropsKey = Object.keys(btn).find(key => key.startsWith('__reactProps$'));
                        if (reactPropsKey && btn[reactPropsKey].onClick) {
                            btn[reactPropsKey].onClick({ preventDefault: () => {}, stopPropagation: () => {} });
                        }
                    }
                }
            }
        }""")
        
        page.wait_for_timeout(2000)
        
        import_btn = page.query_selector("button:has-text('Importar times')")
        p(f"Importar times found? {import_btn is not None}")
        
        if import_btn:
            p("Uploading file...")
            page.set_input_files("input[type='file'][accept='.json']", json_file)
            page.wait_for_timeout(2000)
            
            p("Saving...")
            # We must click "Avançar" if it's there
            avancar = page.query_selector("button:has-text('Avançar')")
            if avancar:
                page.evaluate("document.querySelector(\"button:has-text('Avançar')\").click()")
                page.wait_for_timeout(1000)
            
            salvar = page.query_selector("button:has-text('Salvar')")
            if salvar:
                page.evaluate("document.querySelector(\"button:has-text('Salvar')\").click()")
                page.wait_for_timeout(3000)
                
            p(f"Bot {bot_id} saved via JSON import!")
            
    browser.close()
