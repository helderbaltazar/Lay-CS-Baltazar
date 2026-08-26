from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import datetime
import config
from analysis.blacklist import get_blacklisted_leagues
from notifications.telegram import send_message
from data.api_football import get_odds
from database.backup import run_backup

from data.api_football import get_fixtures
from models.poisson import PoissonDixonColes
from analysis.scanner import scan_all, rank_by_target, save_to_db
from analysis.resolver import resolve_pending_matches
from database.db import SessionLocal

def run_daily_scan():
    print(f"[{datetime.datetime.now()}] Iniciando scan (Hoje e Amanha)...")
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today = now_br.strftime("%Y-%m-%d")
    tomorrow = (now_br + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    dates_to_scan = [today, tomorrow]
    model = PoissonDixonColes()
    db = SessionLocal()
    
    try:
        for d in dates_to_scan:
            print(f"Buscando jogos para a data: {d}")
            fixtures = get_fixtures(d)
            if not fixtures:
                print(f"Nenhum jogo importante encontrado para {d}.")
                continue
                
            results = scan_all(fixtures, model)
            rankings = rank_by_target(results)
            save_to_db(db, rankings)
        print(f"[{datetime.datetime.now()}] Scan (Hoje e Amanha) concluido e salvo com sucesso.")
    finally:
        db.close()

def run_daily_resolve():
    print(f"[{datetime.datetime.now()}] Iniciando resolver de resultados...")
    yesterday = (datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE)) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    count = resolve_pending_matches(yesterday)
    print(f"[{datetime.datetime.now()}] Resolver finalizado. {count} jogos atualizados.")

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.timezone(config.SCHEDULER_TIMEZONE))
    # Executa a meia noite e 1 da manha
    scheduler.add_job(run_daily_scan, 'cron', hour=0, minute=0)
    scheduler.add_job(run_daily_scan, 'cron', hour=1, minute=0)
    # Executa as 4 da manha do dia seguinte
    scheduler.add_job(run_daily_resolve, 'cron', hour=4, minute=0)
    scheduler.start()
    return scheduler

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
        
    msg = f"🏆 *Bom dia! Top 3 Jogos Lay 0-1 de Hoje* ({date_str})\n\n"
    
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
            
        msg += f"*{idx+1}. {m.home_team} x {m.away_team}*\n"
        msg += f"🏅 Liga: {m.league_name}\n"
        msg += f"📊 Prob: {p.probability*100:.2f}%\n"
        msg += f"📈 Odd Mercado: {odd_str} | 💰 Stake sugerida: {stake_str}\n\n"
        
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
            msg = f"✅ *Fechamento do Dia ({today})*\n\n"
            msg += f"Total Finalizados: {stats.total}\n"
            msg += f"✅ GREENS: {stats.greens}\n"
            msg += f"❌ REDS: {stats.reds}\n\n"
            msg += "Boa noite e até amanhã!"
            send_message(msg)
    finally:
        db.close()
