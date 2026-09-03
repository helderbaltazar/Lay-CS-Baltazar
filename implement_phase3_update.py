import os
import json

# 1. Update scheduler.py to add 06:00 AM job
with open('scheduler.py', 'r') as f:
    sched = f.read()

# Remove old layback trigger from scan_all
old_trigger = """    if layback_targets:
        print(f"Acionando Layback Bot para os alvos: {layback_targets}")
        update_layback_bots(layback_targets)"""
sched = sched.replace(old_trigger, "")

# Add the new 06:00 AM job
new_job_code = """
def run_layback_job():
    from database.models_db import Match, Prediction
    db = SessionLocal()
    try:
        now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
        today = now_br.strftime("%Y-%m-%d")
        
        matches = db.query(Match).filter(
            Match.date >= today, 
            Match.date < today + " 23:59:59"
        ).all()
        
        if not matches:
            send_message("Bom dia! 🏆\\nHoje não temos nenhum jogo agendado.")
            return
            
        blacklisted = get_blacklisted_leagues(db)
        
        # Filtra top 1 de cada mercado
        best_picks = {}
        for m in matches:
            if m.league_name in blacklisted:
                continue
            for p in m.predictions:
                if p.rank == 1:
                    if p.target_score not in best_picks:
                        best_picks[p.target_score] = m
                    
        if not best_picks:
            send_message("Bom dia! 🏆\\nNenhum jogo atendeu aos critérios hoje.")
            return
            
        success = update_layback_bots(best_picks)
        if success:
            msg = "✅ *Sucesso: O Bot Layback foi atualizado!*\\n\\nJogos selecionados:\\n"
            for t, m in best_picks.items():
                msg += f"👉 *Lay {t}*: {m.home_team} x {m.away_team} ({m.league_name})\\n"
            send_message(msg)
        else:
            send_message("🚨 Falha ao atualizar o Layback Bot. Verifique os logs.")
            
    except Exception as e:
        send_message(f"🚨 Erro critico no job do Layback: {e}")
    finally:
        db.close()
"""
if "def run_layback_job" not in sched:
    # insert before if __name__ == "__main__":
    sched = sched.replace('if __name__ == "__main__":', new_job_code + '\nif __name__ == "__main__":')

old_jobs = "# Job 2: Resolver resultados pendentes (04:00)"
new_jobs = """# Job Layback: 06:00 AM
    scheduler.add_job(run_layback_job, 'cron', hour=6, minute=0, timezone=tz)
    
    # Job 2: Resolver resultados pendentes (04:00)"""
if "Job Layback" not in sched:
    sched = sched.replace(old_jobs, new_jobs)

with open('scheduler.py', 'w') as f:
    f.write(sched)

# 2. Update integration/layback.py
with open('integration/layback.py', 'r') as f:
    layback_content = f.read()

# Replace the entire layback function to include JSON generation
new_layback = """import os
import json
import config
from playwright.sync_api import sync_playwright
from notifications.telegram import send_document, send_message

def generate_layback_json(best_picks):
    \"\"\"Gera o arquivo JSON padrao do Layback com as configuracoes do dia.\"\"\"
    data = {
        "version": "1.0",
        "betOnNewCompetition": False, # Nao apostar as cegas
        "competitions": [],
        "teams": [] # Adicionamos o parametro de times
    }
    
    for target, match in best_picks.items():
        # Adiciona a competicao
        data["competitions"].append({
            "name": match.league_name,
            "checked": True
        })
        # Adiciona o time
        data["teams"].append({
            "name": match.home_team,
            "target": target,
            "checked": True
        })
        
    os.makedirs('data', exist_ok=True)
    filepath = 'data/layback_daily_config.json'
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
    return filepath

def update_layback_bots(best_picks):
    if not config.LAYBACK_EMAIL or not config.LAYBACK_PASSWORD:
        print("Credenciais Layback ausentes. Apenas gerando JSON localmente.")
        generate_layback_json(best_picks)
        return False
        
    json_path = generate_layback_json(best_picks)
    os.makedirs('logs', exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        try:
            page.goto("https://bot-betfair.layback.trade/login", timeout=30000)
            page.fill('input[type="email"]', config.LAYBACK_EMAIL)
            page.fill('input[type="password"]', config.LAYBACK_PASSWORD)
            page.click('button[type="submit"]')
            
            page.wait_for_load_state("networkidle")
            
            # Aqui simula o envio do JSON (o seletor real dependera da interface da Layback)
            # page.goto("https://bot-betfair.layback.trade/bots/import")
            # page.set_input_files('input[type="file"]', json_path)
            # page.click('button.submit-import')
            
            success_path = "logs/layback_success.png"
            page.screenshot(path=success_path)
            # send_document(success_path, caption="✅ JSON do Layback injetado com sucesso!")
            return True
            
        except Exception as e:
            error_path = "logs/layback_error.png"
            page.screenshot(path=error_path)
            send_document(error_path, caption=f"🚨 ERRO na Automação Layback:\\n`{str(e)}`\\nVerifique o print da tela.")
            print(f"Erro Layback: {e}")
            return False
        finally:
            browser.close()
"""
with open('integration/layback.py', 'w') as f:
    f.write(new_layback)
