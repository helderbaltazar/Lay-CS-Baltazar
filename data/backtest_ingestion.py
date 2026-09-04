import os
import csv
import argparse
from database.db import SessionLocal
from database.models_db import Match, Prediction
import datetime

def ingest_csv(filepath, league_name):
    """
    Ingere dados de backtest a partir de um arquivo CSV (estilo football-data.co.uk).
    """
    print(f"Ingerindo dados do arquivo {filepath} para a liga {league_name}...")
    db = SessionLocal()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    date_str = row.get('Date', '')
                    if not date_str:
                        continue
                    
                    # O formato da data pode variar: DD/MM/YYYY ou YYYY-MM-DD
                    if '/' in date_str:
                        date_obj = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
                    else:
                        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                        
                    home_team = row.get('HomeTeam', 'Unknown')
                    away_team = row.get('AwayTeam', 'Unknown')
                    fthg = row.get('FTHG', '0')
                    ftag = row.get('FTAG', '0')
                    real_score = f"{fthg}-{ftag}"
                    
                    # Cria um ID de fixture ficticio se nao houver da API
                    fixture_id = int(date_obj.strftime("%Y%m%d")) + hash(home_team) % 1000000
                    
                    # Verifica se ja existe
                    exists = db.query(Match).filter_by(fixture_id=fixture_id).first()
                    if exists:
                        continue
                        
                    match = Match(
                        fixture_id=fixture_id,
                        date=date_obj,
                        league_name=league_name,
                        home_team=home_team,
                        away_team=away_team,
                        status="FT",
                        real_score=real_score
                    )
                    db.add(match)
                    count += 1
                except Exception as e:
                    print(f"Erro ao processar linha: {e}")
                    continue
            db.commit()
            print(f"Ingestão concluída. {count} partidas adicionadas.")
    except Exception as e:
        print(f"Erro fatal: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestão de dados históricos para backtest")
    parser.add_argument("--csv", help="Caminho para o arquivo CSV", required=True)
    parser.add_argument("--league", help="Nome da liga", required=True)
    
    args = parser.parse_args()
    if args.csv and os.path.exists(args.csv):
        ingest_csv(args.csv, args.league)
    else:
        print("Arquivo CSV não encontrado.")
