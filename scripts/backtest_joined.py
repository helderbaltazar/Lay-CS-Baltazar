import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.poisson import PoissonDixonColes

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT h.MatchDate, h.HomeTeam, h.AwayTeam, h.FTHome, h.FTAway, 
           h.Under25, h.Over25, h.HomeTarget, h.AwayTarget,
           t.team_a_xg, t.team_b_xg, t.odds_ft_under25 as tel_odd_under, t.odds_ft_over25 as tel_odd_over
    FROM historical_dataset h
    INNER JOIN telegram_dataset t 
    ON h.HomeTeam = t.home_name 
       AND h.AwayTeam = t.away_name 
       AND strftime('%Y-%m-%d', h.MatchDate) = substr(t.Data_Hora_Jogo, 7, 4) || '-' || substr(t.Data_Hora_Jogo, 4, 2) || '-' || substr(t.Data_Hora_Jogo, 1, 2)
    WHERE h.HomeTarget IS NOT NULL 
      AND h.AwayTarget IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

print(f"Jogos cruzados com sucesso: {len(df)}")
if len(df) > 0:
    print(df.head())
