from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import datetime
import config
from data.api_football import get_fixtures
from models.poisson import PoissonDixonColes
from analysis.scanner import scan_all, rank_by_target, save_to_db
from analysis.resolver import resolve_pending_matches
from database.db import SessionLocal

def run_daily_scan():
    print(f"[{datetime.datetime.now()}] Iniciando scan diario...")
    today = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE)).strftime("%Y-%m-%d")
    fixtures = get_fixtures(today)
    if not fixtures:
        print("Nenhum jogo encontrado para hoje ou cota de API excedida.")
        return
        
    model = PoissonDixonColes()
    results = scan_all(fixtures, model)
    rankings = rank_by_target(results)
    
    db = SessionLocal()
    try:
        save_to_db(db, rankings)
        print(f"[{datetime.datetime.now()}] Scan salvo com sucesso.")
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
