import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models.poisson import PoissonDixonColes

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT MatchDate, HomeTeam, AwayTeam, FTHome, FTAway, 
           Under25, Over25, HomeTarget, AwayTarget
    FROM historical_dataset
    WHERE MatchDate LIKE '2026-08-29%' OR MatchDate LIKE '2026-08-30%'
      AND HomeTarget IS NOT NULL 
      AND AwayTarget IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

model = PoissonDixonColes(rho=-0.10)
print(f"Jogos no banco histórico para o último FDS de Agosto: {len(df)}")

print("\n=== OVER 2.5 (Nota >= 90) ===")
for idx, row in df.iterrows():
    probs = model.get_extra_probabilities(float(row['HomeTarget']), float(row['AwayTarget']))
    score = probs["OVER_2.5"] * 100
    if score >= 90:
        total_goals = int(row['FTHome']) + int(row['FTAway'])
        hit = "GREEN" if total_goals > 2.5 else "RED"
        odd = row.get("Over25")
        print(f"[{row['MatchDate'][:10]}] {row['HomeTeam']} {row['FTHome']}x{row['FTAway']} {row['AwayTeam']} | Score: {score:.1f} | Resultado: {hit} (Odd: {odd})")

print("\n=== UNDER 2.5 (Nota >= 85) ===")
for idx, row in df.iterrows():
    probs = model.get_extra_probabilities(float(row['HomeTarget']), float(row['AwayTarget']))
    score = probs["UNDER_2.5"] * 100
    if score >= 85:
        total_goals = int(row['FTHome']) + int(row['FTAway'])
        hit = "GREEN" if total_goals < 2.5 else "RED"
        odd = row.get("Under25")
        print(f"[{row['MatchDate'][:10]}] {row['HomeTeam']} {row['FTHome']}x{row['FTAway']} {row['AwayTeam']} | Score: {score:.1f} | Resultado: {hit} (Odd: {odd})")
