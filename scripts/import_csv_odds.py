import requests
import csv
import io
from database.db import SessionLocal
from database.models_db import Match, Prediction

# Mapeamento do football-data.co.uk
CSV_LINKS = {
    'Premier League': 'https://www.football-data.co.uk/mmz4281/2324/E0.csv',
    'La Liga': 'https://www.football-data.co.uk/mmz4281/2324/SP1.csv',
    'Serie A': 'https://www.football-data.co.uk/mmz4281/2324/I1.csv',
}

def import_historical_odds():
    db = SessionLocal()
    updated = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/110.0'}

    for league_name, url in CSV_LINKS.items():
        print(f"Baixando dados para {league_name}...")
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Erro ao baixar {url} (Status: {response.status_code})")
                continue
                
            content = response.content.decode('utf-8', errors='ignore')
            reader = csv.DictReader(io.StringIO(content))
            
            for row in reader:
                home = row.get('HomeTeam')
                away = row.get('AwayTeam')
                if not home or not away: continue
                    
                over25_odd = row.get('B365>2.5') or row.get('P>2.5')
                under25_odd = row.get('B365<2.5') or row.get('P<2.5')
                
                # Match logic
                match = db.query(Match).filter(
                    Match.home_team.like(f"%{home[:5]}%"),
                    Match.league_name.like(f"%{league_name[:4]}%")
                ).first()
                
                if match and over25_odd:
                    preds = db.query(Prediction).filter(Prediction.match_id == match.id).all()
                    for p in preds:
                        if p.target_score == "OVER_2.5":
                            p.match_odd = float(over25_odd)
                            updated += 1
                        elif p.target_score == "UNDER_2.5":
                            p.match_odd = float(under25_odd)
                            updated += 1
                    
        except Exception as e:
            print(f"Falha ao processar {league_name}: {e}")
            
    db.commit()
    db.close()
    print(f"Importação concluída. {updated} predições atualizadas com odds históricas.")

if __name__ == "__main__":
    import_historical_odds()
