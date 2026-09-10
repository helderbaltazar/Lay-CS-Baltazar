import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.poisson import PoissonDixonColes

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        homeGoalCount, awayGoalCount,
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_Total_Casa IS NOT NULL 
      AND Media_Gols_Total_Visitante IS NOT NULL
      AND homeGoalCount IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

model = PoissonDixonColes()

probs = []
for _, row in df.iterrows():
    h = row['Media_Gols_Total_Casa']
    a = row['Media_Gols_Total_Visitante']
    if h <= 0: h = 0.1
    if a <= 0: a = 0.1
    matrix = model.predict(h, a)
    probs.append(matrix.get((0, 1), 0))

df['Power_0_1'] = [(1 - p) * 100 for p in probs]
df['Losses'] = ((df['homeGoalCount'] == 0) & (df['awayGoalCount'] == 1)).astype(int)

def evaluate_cutoff(min_val, max_val):
    sub = df[(df['Power_0_1'] >= min_val) & (df['Power_0_1'] <= max_val)]
    t = len(sub)
    if t == 0:
        return f"Power Score {min_val} - {max_val}: Sem jogos."
    losses = sub['Losses'].sum()
    wins = t - losses
    wr = wins / t
    lucro = (wins * 100) - (losses * 100 * 11)  # Odd 12 (Risca 11)
    roi = (lucro / (t*100)) * 100
    return f"Power Score >= {min_val}: Volume = {t} | Win Rate = {wr*100:.2f}% | Lucro = R$ {lucro:.2f} | ROI = {roi:.2f}%"

print("--- ANALISE DE CORTE LAY CS 0-1 ---")
print(evaluate_cutoff(97.0, 100.0))
print(evaluate_cutoff(98.0, 100.0))
print(evaluate_cutoff(98.5, 100.0))
print(evaluate_cutoff(99.0, 100.0))
print(evaluate_cutoff(99.2, 100.0))
print(evaluate_cutoff(99.5, 100.0))
print(evaluate_cutoff(99.9, 100.0))
