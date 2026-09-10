import config
from database.db import SessionLocal
from database.models_db import Match, Prediction
import json
from difflib import get_close_matches
import soccerdata as sd
import time

def fetch_and_update():
    print("Inicializando scraper do football-data.co.uk (soccerdata)...")
    try:
        # Puxa os dados das ligas de topo (EPL, LaLiga, Serie A, etc) para a temporada atual
        # FB-Data leagues: ENG-Premier League, ESP-La Liga, ITA-Serie A, GER-Bundesliga, FRA-Ligue 1
        fb = sd.MatchHistory(leagues=["ENG-Premier League", "ESP-La Liga", "ITA-Serie A", "GER-Bundesliga", "FRA-Ligue 1"], seasons="2026")
        df = fb.read_games()
    except Exception as e:
        print(f"Erro ao baixar CSVs do football-data: {e}")
        return
        
    print(f"CSVs baixados! {len(df)} jogos encontrados.")
    
    db = SessionLocal()
    matches = db.query(Match).all()
    updated = 0
    
    for m in matches:
        if m.odds_data:
            continue
            
        found = False
        # O dataframe do soccerdata tem (game_id, date, home_team, away_team, B365H, B365D, B365A, etc)
        # B365H = Bet365 Home Odd, B365D = Draw, B365A = Away
        for index, row in df.iterrows():
            fb_home = row.get('home_team', '')
            fb_away = row.get('away_team', '')
            
            # Fuzzy match
            if (get_close_matches(m.home_team, [fb_home], n=1, cutoff=0.5) and 
                get_close_matches(m.away_team, [fb_away], n=1, cutoff=0.5)):
                
                # Pegar odd Bet365 (B365H) ou Pinnacle (PSH)
                home_odd = row.get('B365H') or row.get('PSH') or row.get('MaxH') or row.get('AvgH')
                draw_odd = row.get('B365D') or row.get('PSD') or row.get('MaxD') or row.get('AvgD')
                away_odd = row.get('B365A') or row.get('PSA') or row.get('MaxA') or row.get('AvgA')
                
                if home_odd and str(home_odd) != 'nan':
                    odds_dict = {'1': home_odd, 'X': draw_odd, '2': away_odd}
                    m.odds_data = json.dumps(odds_dict)
                    
                    for p in m.predictions:
                        p.match_odd = home_odd
                        
                    updated += 1
                    break
                    
    db.commit()
    db.close()
    print(f"✅ Histórico do football-data atualizado: {updated} jogos enriquecidos!")

if __name__ == "__main__":
    fetch_and_update()
