import datetime
import pytz
import json
import difflib
import config
from data.api_football import get_fixtures
from models.poisson import PoissonDixonColes
from analysis.scanner import scan_all, rank_by_target
from integration.layback import generate_layback_json, inject_teams_ui, LAY_0_1_BOT_ID, LAY_0_2_BOT_ID, LAY_0_3_BOT_ID

def get_betfair_id(team_name, layback_teams):
    names = [t["name"] for t in layback_teams]
    # Exact match first
    if team_name in names:
        team = next((t for t in layback_teams if t["name"] == team_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    # Replace common differences
    replacements = {
        " FC": "",
        "FC ": "",
        " CF": "",
        " Clube": "",
        " Esporte": "",
        " SP": "",
        " RJ": "",
        " MG": "",
        " RS": "",
        " PR": "",
        " SC": "",
        " BA": "",
        " GO": "",
        " CE": "",
        " PE": "",
        " RN": "",
        " PB": "",
        " AL": "",
        " SE": "",
        " PI": "",
        " MA": "",
        " TO": "",
        " PA": "",
        " AM": "",
        " RR": "",
        " AC": "",
        " AP": "",
        " RO": "",
        " MT": "",
        " MS": "",
        " DF": "",
        " ES": "",
        "Atletico Mineiro": "Atletico MG",
        "Athletico Paranaense": "Atletico PR",
        "Atletico Paranaense": "Atletico PR",
        "Atletico Goianiense": "Atletico GO",
        "Botafogo RJ": "Botafogo",
        "Fluminense RJ": "Fluminense",
        "Flamengo RJ": "Flamengo",
        "Vasco da Gama": "Vasco da Gama",
        "Vasco": "Vasco da Gama",
        "Cruzeiro": "Cruzeiro MG",
        "Gremio": "Gremio",
        "Internacional": "Internacional",
        "Corinthians": "Corinthians",
        "Palmeiras": "Palmeiras",
        "Santos": "Santos",
        "Sao Paulo": "Sao Paulo",
    }
    
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
    print(f"[{datetime.datetime.now()}] Iniciando extração e injeção (Hoje e Amanhã)...")
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today = now_br.strftime("%Y-%m-%d")
    tomorrow = (now_br + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    dates_to_scan = [today, tomorrow]
    model = PoissonDixonColes()
    
    all_fixtures = []
    for d in dates_to_scan:
        print(f"Buscando jogos para a data: {d}")
        f = get_fixtures(d)
        if f:
            all_fixtures.extend(f)
            
    if not all_fixtures:
        print("Nenhum jogo encontrado nas ligas configuradas.")
        return
        
    print(f"Encontrados {len(all_fixtures)} jogos. Calculando Poisson...")
    results = scan_all(all_fixtures, model)
    rankings = rank_by_target(results)
    
    # Carregar base de times do Layback
    with open("logs/teams_api.json", "r") as f:
        layback_teams = json.load(f)["data"]["teams"]
        
    # Extrair Rank 1 de cada placar
    rank1_01 = [r for r in rankings["0-1"] if r["rank"] <= 2]
    rank1_02 = [r for r in rankings["0-2"] if r["rank"] <= 2]
    rank1_03 = [r for r in rankings["0-3"] if r["rank"] <= 2]
    
    bots_targets = [
        (LAY_0_1_BOT_ID, "bot_lay_0_1", rank1_01, "0-1"),
        (LAY_0_2_BOT_ID, "bot_lay_0_2", rank1_02, "0-2"),
        (LAY_0_3_BOT_ID, "bot_lay_0_3", rank1_03, "0-3"),
    ]
    
    print("\n--- RESUMO DA SELEÇÃO ---")
    for bot_id, bot_name, rank_list, target in bots_targets:
        if not rank_list:
            print(f"[{target}] Nenhum jogo qualificado.")
            continue
            
        teams_data = []
        for game in rank_list:
            print(f"[{target}] Rank {game['rank']}: {game['home']} x {game['away']} (Prob: {game['probability']:.2%})")
            
            # Mapear IDs
            home_bf = get_betfair_id(game['home'], layback_teams)
            away_bf = get_betfair_id(game['away'], layback_teams)
            
            if home_bf:
                teams_data.append(home_bf)
            if away_bf:
                teams_data.append(away_bf)
            
        if not teams_data:
            print(f"ERRO: Não foi possível mapear nenhum dos times para a Betfair!")
            continue
            
        print(f"[{target}] Mapeados Betfair: {[t['name'] for t in teams_data]}")
        
        # Gerar JSON
        json_file = generate_layback_json(teams_data, bot_name)
        
        # Injetar UI
        print(f"[{target}] Injetando no bot {bot_id}...")
        success = inject_teams_ui(bot_id, json_file)
        if success:
            print(f"[{target}] SUCESSO na injeção!")
        else:
            print(f"[{target}] FALHA na injeção.")

if __name__ == "__main__":
    main()
