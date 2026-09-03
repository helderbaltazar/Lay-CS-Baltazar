import config
import json
from playwright.sync_api import sync_playwright

# Precisamos interceptar os requests ENQUANTO clicamos no Editar de Times no browser real
# Vamos fazer isso com intercepção de responses também

PUT_PATCH_reqs = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    
    def on_request(request):
        if request.method in ["PUT", "PATCH", "POST", "DELETE"] and "bot-betfair" in request.url and "auth" not in request.url:
            entry = {
                "method": request.method,
                "url": request.url,
                "body": request.post_data or ""
            }
            PUT_PATCH_reqs.append(entry)
            print(f"*** [{request.method}] {request.url}")
            if request.post_data:
                print(f"  Body: {request.post_data[:600]}")
    
    page.on("request", on_request)
    
    # Login
    page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
    with page.expect_navigation():
        page.click("text='Continuar com Betfair'")
    page.wait_for_selector("#username", timeout=15000)
    page.fill('#username', config.LAYBACK_EMAIL)
    page.fill('#password', config.LAYBACK_PASSWORD)
    page.click('#login')
    page.wait_for_selector("[href='/dashboard'], [href*='/bots']", timeout=30000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    
    # Navega ao bot 150
    page.goto("https://bot-betfair.layback.trade/bots/150")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(5000)
    
    # Clica na aba "Configuração"
    page.click("button:has-text('Configuração')")
    page.wait_for_timeout(3000)
    
    # Rola até seção de Times
    page.evaluate("""() => {
        const divs = document.querySelectorAll("div");
        for (let div of divs) {
            if (div.className.includes("rounded-[inherit]") && div.scrollHeight > div.clientHeight) {
                div.scrollTop = 1200;
                break;
            }
        }
    }""")
    page.wait_for_timeout(2000)
    page.screenshot(path="logs/before_times_click.png")
    
    # Clica no botão Editar na seção de Times e espera o modal
    print("Tentando clicar no Editar de Times...")
    clicked = page.evaluate("""() => {
        // Percorre todos os elementos buscando 'Times' com caso insensitive
        const sections = document.querySelectorAll("div");
        for (let sec of sections) {
            if (sec.textContent.includes("Times para apostar") && sec.querySelectorAll("button").length > 0) {
                const buttons = sec.querySelectorAll("button");
                for (let b of buttons) {
                    if (b.textContent.trim().includes("Editar")) {
                        // Antes de clicar, vamos verificar posição
                        const rect = b.getBoundingClientRect();
                        console.log("Botão Editar de Times encontrado em:", JSON.stringify(rect));
                        b.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                        return {found: true, text: b.textContent, rect: JSON.stringify(rect)};
                    }
                }
            }
        }
        return {found: false};
    }""")
    print(f"Resultado do clique: {clicked}")
    page.wait_for_timeout(5000)
    page.screenshot(path="logs/after_times_click.png")
    
    # Captura o estado atual da pagina - verifica se abriu modal
    modal_found = page.query_selector('[role="dialog"]')
    print(f"Modal encontrado: {modal_found is not None}")
    
    if modal_found:
        print("Modal HTML:")
        print(modal_found.inner_html()[:2000])
    
    print(f"\nRequests PUT/PATCH capturadas: {len(PUT_PATCH_reqs)}")
    for r in PUT_PATCH_reqs:
        print(f"  {r['method']} {r['url']}")
        print(f"  Body: {r['body'][:400]}")
    
    with open("logs/intercept_requests.json", "w") as f:
        json.dump(PUT_PATCH_reqs, f, indent=2)
    
    browser.close()
