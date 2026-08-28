import datetime
import pytz
import config
from database.db import SessionLocal
from database.models_db import Match, Prediction
from analysis.scanner import scan_all, rank_by_target, save_to_db
from models.poisson import PoissonDixonColes
from data.api_football import get_fixtures
import json
import difflib
from integration.layback import generate_layback_json, inject_teams_ui, LAY_0_1_BOT_ID, LAY_0_2_BOT_ID, LAY_0_3_BOT_ID, LAY_1_3_BOT_ID

def get_betfair_id(team_name, layback_teams):
    names = [t["name"] for t in layback_teams]
    if team_name in names:
        team = next((t for t in layback_teams if t["name"] == team_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    replacements = {" FC": "", "FC ": "", " CF": "", " Clube": "", " Esporte": ""}
    modified_name = team_name
    for k, v in replacements.items():
        if k in modified_name:
            modified_name = modified_name.replace(k, v).strip()
            
    if modified_name in names:
        team = next((t for t in layback_teams if t["name"] == modified_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    matches = difflib.get_close_matches(team_name, names, n=1, cutoff=0.6)
    if matches:
        match_name = matches[0]
        team = next((t for t in layback_teams if t["name"] == match_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    return None

def ensure_data_in_db():
    db = SessionLocal()
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today_start = now_br.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"[{now_br}] Verificando se os jogos de hoje já estão no Supabase...")
    matches_today = db.query(Match).filter(Match.date >= today_start).first()
    
    if matches_today:
        print("✅ Jogos do dia já existem no banco de dados. Pulando a extração da API...")
    else:
        print("⚠️ Nenhum jogo encontrado no banco para hoje. Buscando na API...")
        today_str = now_br.strftime("%Y-%m-%d")
        all_fixtures = []
        f = get_fixtures(today_str)
        if f:
            all_fixtures.extend(f)
                
        if all_fixtures:
            model = PoissonDixonColes()
            results = scan_all(all_fixtures, model)
            rankings = rank_by_target(results)
            save_to_db(db, rankings)
            print("✅ Novos jogos calculados e salvos no banco de dados com sucesso.")
        else:
            print("❌ Nenhum jogo configurado nas ligas para hoje/amanhã retornado pela API.")
    
    db.close()

def inject_from_db():
    print("\\n--- INICIANDO INJEÇÃO NO LAYBACK VIA BANCO DE DADOS ---")
    db = SessionLocal()
    
    with open("data/teams_api.json", "r") as f:
        layback_teams = json.load(f)["data"]["teams"]

    targets = [
        (LAY_0_1_BOT_ID, "bot_lay_0_1", "0-1"),
        (LAY_0_2_BOT_ID, "bot_lay_0_2", "0-2"),
        (LAY_0_3_BOT_ID, "bot_lay_0_3", "0-3"),
        (LAY_1_3_BOT_ID, "bot_lay_1_3", "1-3"),
    ]
    
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today_start = now_br.replace(hour=0, minute=0, second=0, microsecond=0)
    
    report_lines = ["🤖 *Relatório Diário Layback* 🤖\n"]
    for bot_id, bot_name, target in targets:
        preds = db.query(Prediction).join(Match).filter(
            Prediction.target_score == target,
            Prediction.rank <= 2,
            Match.date >= today_start
        ).order_by(Prediction.rank).limit(2).all()
        
        if not preds:
            print(f"[{target}] Nenhum jogo no banco para hoje/amanhã.")
            continue
            
        bot_games_str = []
        teams_data = []
        for p in preds:
            m = p.match
            print(f"[{target}] Rank {p.rank}: {m.home_team} x {m.away_team} (Prob: {p.probability:.2%})")
            bot_games_str.append(f"⚽ {m.home_team} x {m.away_team} ({p.probability:.2%})")
            h_bf = get_betfair_id(m.home_team, layback_teams)
            a_bf = get_betfair_id(m.away_team, layback_teams)
            if h_bf: teams_data.append(h_bf)
            if a_bf: teams_data.append(a_bf)
            
        if not teams_data:
            print(f"ERRO: Não mapeou nenhum time!")
            continue
            
        json_file = generate_layback_json(teams_data, bot_name)
        print(f"[{target}] Injetando no bot {bot_id} via Playwright...")
        success = inject_teams_ui(bot_id, json_file)
        if success:
            report_lines.append(f"✅ *{target}* (Bot {bot_id}):")
            report_lines.extend(bot_games_str)
            report_lines.append("")
            print(f"[{target}] SUCESSO!")
        else:
            report_lines.append(f"❌ *{target}* (Bot {bot_id}) FALHOU.")
            report_lines.append("")
            print(f"[{target}] FALHOU!")
            final_report = "\n".join(report_lines)
            from notifications.telegram import send_message
            send_message(final_report)
            import sys
            sys.exit(1)
            
    final_report = "\n".join(report_lines)
    from notifications.telegram import send_message
    send_message(final_report)
    db.close()

if __name__ == "__main__":
    try:
        from update_results import update_pending_matches
        update_pending_matches()
    except Exception as e:
        print(f"Erro ao atualizar pendentes: {e}")
        
    ensure_data_in_db()
    inject_from_db()
