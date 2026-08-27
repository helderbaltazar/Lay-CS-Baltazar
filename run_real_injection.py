import json
import difflib
from integration.layback import generate_layback_json, inject_teams_ui, LAY_0_1_BOT_ID, LAY_0_2_BOT_ID, LAY_0_3_BOT_ID
from database.db import SessionLocal
from database.models_db import Match, Prediction
from sqlalchemy import desc
import datetime
import pytz
import config

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

def main():
    print("Forçando teste de injeção a partir do Banco de Dados...")
    db = SessionLocal()
    
    with open("logs/teams_api.json", "r") as f:
        layback_teams = json.load(f)["data"]["teams"]

    targets = [
        (LAY_0_1_BOT_ID, "bot_lay_0_1", "0-1"),
        (LAY_0_2_BOT_ID, "bot_lay_0_2", "0-2"),
        (LAY_0_3_BOT_ID, "bot_lay_0_3", "0-3"),
    ]
    
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today_start = now_br.replace(hour=0, minute=0, second=0, microsecond=0)
    
    for bot_id, bot_name, target in targets:
        # Puxa os 2 primeiros (rank 1 e 2) do banco para este placar filtrando por jogos a partir de hoje
        preds = db.query(Prediction).join(Match).filter(
            Prediction.target_score == target,
            Prediction.rank <= 2,
            Match.date >= today_start
        ).order_by(Prediction.rank).limit(2).all()
        if not preds:
            print(f"[{target}] Nenhum jogo no banco.")
            continue
            
        teams_data = []
        for p in preds:
            m = p.match
            print(f"[{target}] Rank {p.rank}: {m.home_team} x {m.away_team} (Prob: {p.probability:.2%})")
            h_bf = get_betfair_id(m.home_team, layback_teams)
            a_bf = get_betfair_id(m.away_team, layback_teams)
            if h_bf: teams_data.append(h_bf)
            if a_bf: teams_data.append(a_bf)
            
        if not teams_data:
            print(f"ERRO: Não mapeou nenhum time!")
            continue
            
        print(f"[{target}] Times a injetar: {[t['name'] for t in teams_data]}")
        json_file = generate_layback_json(teams_data, bot_name)
        
        print(f"[{target}] Injetando no bot {bot_id} via Playwright...")
        success = inject_teams_ui(bot_id, json_file)
        if success:
            print(f"[{target}] SUCESSO!")
        else:
            print(f"[{target}] FALHOU!")
            
    db.close()

if __name__ == "__main__":
    main()
