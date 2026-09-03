import config
import json
from playwright.sync_api import sync_playwright

PUT_PATCH_reqs = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # Viewport muito alto para que os elementos fiquem visíveis
    context = browser.new_context(viewport={'width': 1440, 'height': 2000})
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
    
    page.screenshot(path="logs/tall_viewport_config.png")
    
    # Verifica qual elemento de Times está visível
    times_btn_info = page.evaluate("""() => {
        const sections = document.querySelectorAll("div");
        let results = [];
        for (let sec of sections) {
            if (sec.textContent.trim() === "Times para apostar") {
                let el = sec.parentElement;
                for (let i = 0; i < 10; i++) {
                    const buttons = el.querySelectorAll("button");
                    for (let b of buttons) {
                        if (b.textContent.trim() === "Editar") {
                            const rect = b.getBoundingClientRect();
                            results.push({
                                level: i,
                                text: b.textContent.trim(),
                                rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height}
                            });
                        }
                    }
                    el = el.parentElement;
                    if (!el) break;
                }
            }
        }
        return results;
    }""")
    print("Botões Editar de Times encontrados:")
    print(json.dumps(times_btn_info, indent=2))
    
    # Clica no primeiro botão Editar que tiver dimensões válidas
    clicked = page.evaluate("""() => {
        const sections = document.querySelectorAll("div");
        for (let sec of sections) {
            if (sec.textContent.trim() === "Times para apostar") {
                let el = sec.parentElement;
                for (let i = 0; i < 10; i++) {
                    const buttons = el.querySelectorAll("button");
                    for (let b of buttons) {
                        if (b.textContent.trim() === "Editar") {
                            const rect = b.getBoundingClientRect();
                            if (rect.width > 0) {
                                b.click();
                                return {found: true, rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height}};
                            }
                        }
                    }
                    el = el.parentElement;
                    if (!el) break;
                }
            }
        }
        return {found: false};
    }""")
    print(f"\nClique resultado: {clicked}")
    page.wait_for_timeout(5000)
    page.screenshot(path="logs/tall_after_click.png")
    
    modal = page.query_selector('[role="dialog"]')
    print(f"Modal encontrado: {modal is not None}")
    if modal:
        print("Modal:")
        print(modal.inner_text()[:1000])
    
    print(f"\nRequests PUT/PATCH: {len(PUT_PATCH_reqs)}")
    for r in PUT_PATCH_reqs:
        print(f"  {r['method']} {r['url']}")
        print(f"  Body: {r['body'][:400]}")
    
    browser.close()
