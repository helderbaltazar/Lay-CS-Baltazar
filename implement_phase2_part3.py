import os

# 1. Add get_odds to data/api_football.py
with open('data/api_football.py', 'r') as f:
    api_content = f.read()

odds_code = """
def get_odds(fixture_id, target_score):
    url = f"{config.BASE_URL}/odds?fixture={fixture_id}&bookmaker=8" # 8 = Bet365
    try:
        response = requests.get(url, headers=get_headers())
        data = response.json()
        if not data.get('response'):
            return None
            
        bookmakers = data['response'][0].get('bookmakers', [])
        if not bookmakers:
            return None
            
        markets = bookmakers[0].get('bets', [])
        for m in markets:
            if m['name'] == 'Exact Score' or m['id'] == 10:
                for val in m['values']:
                    if val['value'] == target_score:
                        return float(val['odd'])
        return None
    except Exception as e:
        print(f"Erro ao buscar odds para fixture {fixture_id}: {e}")
        return None
"""
if "def get_odds" not in api_content:
    api_content += odds_code
    with open('data/api_football.py', 'w') as f:
        f.write(api_content)
    print("Função get_odds adicionada.")

# 2. Update scheduler.py to integrate Telegram, Backups, Blacklist, and Stake calculation
with open('scheduler.py', 'r') as f:
    sched_content = f.read()

new_imports = """
from analysis.blacklist import get_blacklisted_leagues
from notifications.telegram import send_message
from data.api_football import get_odds
from database.backup import run_backup
"""
sched_content = sched_content.replace("import config", "import config" + new_imports)

old_run_scan = """                results = scan_all(fixtures, model)
                rankings = rank_by_target(results)
                save_to_db(db, rankings)
            print(f"[{datetime.datetime.now()}] Scan (Hoje e Amanha) concluido e salvo com sucesso.")
        finally:
            db.close()"""
            
new_run_scan = """                results = scan_all(fixtures, model)
                rankings = rank_by_target(results)
                save_to_db(db, rankings)
            print(f"[{datetime.datetime.now()}] Scan (Hoje e Amanha) concluido e salvo com sucesso.")
            
            # Etapa Telegram (Morning Alert) e Blacklist
            # Apenas envia no scan de 01:00 da manha (para evitar spammeio duplo)
            if now_br.hour in [0, 1]:
                send_morning_alert(db, today)
                
        except Exception as e:
            send_message(f"⚠️ *Alerta Crítico Lay CS*\nErro durante a varredura (Scan): `{e}`")
            raise
        finally:
            db.close()"""
sched_content = sched_content.replace(old_run_scan, new_run_scan)

morning_alert_code = """
def send_morning_alert(db, date_str):
    from database.models_db import Match, Prediction
    
    blacklisted = get_blacklisted_leagues(db)
    
    matches = db.query(Match).filter(
        Match.date >= date_str, 
        Match.date < date_str + " 23:59:59"
    ).all()
    
    if not matches:
        return
        
    # Filtrar blacklist e buscar os 3 melhores (menor rank)
    top_picks = []
    for m in matches:
        if m.league_name in blacklisted:
            continue
            
        for p in m.predictions:
            if p.target_score == '0-1': # Foco da mensagem no 0-1
                top_picks.append({'match': m, 'pred': p})
                
    top_picks.sort(key=lambda x: x['pred'].rank or 9999)
    top_3 = top_picks[:3]
    
    if not top_3:
        send_message("Bom dia! 🏆\nHoje não temos nenhum jogo seguro fora da Blacklist para o método Lay 0-1.")
        return
        
    msg = f"🏆 *Bom dia! Top 3 Jogos Lay 0-1 de Hoje* ({date_str})\\n\\n"
    
    liability = config.BANKROLL * (config.MAX_LIABILITY / 100)
    
    for idx, item in enumerate(top_3):
        m = item['match']
        p = item['pred']
        
        odd = get_odds(m.fixture_id, '0-1')
        odd_str = f"{odd}" if odd else "N/A"
        
        stake_str = "N/A"
        if odd and odd > 1.0:
            stake = liability / (odd - 1)
            stake_str = f"R$ {stake:.2f}"
            
        msg += f"*{idx+1}. {m.home_team} x {m.away_team}*\\n"
        msg += f"🏅 Liga: {m.league_name}\\n"
        msg += f"📊 Prob: {p.probability*100:.2f}%\\n"
        msg += f"📈 Odd Mercado: {odd_str} | 💰 Stake sugerida: {stake_str}\\n\\n"
        
    msg += f"*(Sua Banca Configurada: R$ {config.BANKROLL:.2f} | Responsabilidade: {config.MAX_LIABILITY}% - R$ {liability:.2f})*"
    send_message(msg)

def send_night_alert():
    # Rodar as 23:50 para sumario do dia
    db = SessionLocal()
    try:
        now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
        today = now_br.strftime("%Y-%m-%d")
        
        from sqlalchemy import func
        from database.models_db import Match, Prediction
        
        stats = db.query(
            func.count(Match.id).label('total'),
            func.sum(func.case((Prediction.is_hit == True, 1), else_=0)).label('greens'),
            func.sum(func.case((Prediction.is_hit == False, 1), else_=0)).label('reds')
        ).join(Prediction).filter(
            Match.date >= today,
            Match.date < today + " 23:59:59",
            Match.status.in_(['FT', 'AET', 'PEN']),
            Prediction.is_hit != None,
            Prediction.target_score == '0-1'
        ).first()
        
        if stats and stats.total > 0:
            msg = f"✅ *Fechamento do Dia ({today})*\\n\\n"
            msg += f"Total Finalizados: {stats.total}\\n"
            msg += f"✅ GREENS: {stats.greens}\\n"
            msg += f"❌ REDS: {stats.reds}\\n\\n"
            msg += "Boa noite e até amanhã!"
            send_message(msg)
    finally:
        db.close()
"""
if "def send_morning_alert" not in sched_content:
    sched_content += morning_alert_code
    
old_jobs = """    # Job 1: Buscar e processar os jogos de hoje (00:00 e 01:00)
    scheduler.add_job(run_daily_scan, 'cron', hour='0,1', minute=0, timezone=tz)
    
    # Job 2: Resolver resultados pendentes (04:00)
    scheduler.add_job(run_daily_resolve, 'cron', hour=4, minute=0, timezone=tz)"""
new_jobs = """    # Job 1: Buscar e processar os jogos de hoje (00:00 e 01:00)
    scheduler.add_job(run_daily_scan, 'cron', hour='0,1', minute=0, timezone=tz)
    
    # Job 2: Resolver resultados pendentes (04:00)
    scheduler.add_job(run_daily_resolve, 'cron', hour=4, minute=0, timezone=tz)
    
    # Job 3: Sumario noturno (23:50)
    scheduler.add_job(send_night_alert, 'cron', hour=23, minute=50, timezone=tz)
    
    # Job 4: Backup semanal (Domingo 03:00)
    scheduler.add_job(run_backup, 'cron', day_of_week='sun', hour=3, minute=0, timezone=tz)"""
sched_content = sched_content.replace(old_jobs, new_jobs)

with open('scheduler.py', 'w') as f:
    f.write(sched_content)
print("Scheduler atualizado com Telegram e Blacklist.")
