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
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante,
        Media_Gols_no_1T_Casa, Media_Gols_no_1T_Visitante,
        Efic_xG_Casa, Efic_xG_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_Total_Casa IS NOT NULL 
      AND Media_Gols_Total_Visitante IS NOT NULL
      AND homeGoalCount IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

model = PoissonDixonColes()

print(f"Dataset Size: {len(df)} matches")

# Evaluate probabilities
probs_0_1 = []
probs_0_2 = []
probs_0_3 = []

for _, row in df.iterrows():
    h_lambda = row['Media_Gols_Total_Casa']
    a_lambda = row['Media_Gols_Total_Visitante']
    
    # Previne valores negativos/zerados que dao erro no Poisson
    if h_lambda <= 0: h_lambda = 0.1
    if a_lambda <= 0: a_lambda = 0.1
    
    matrix = model.predict(h_lambda, a_lambda)
    
    probs_0_1.append(matrix.get((0, 1), 0))
    probs_0_2.append(matrix.get((0, 2), 0))
    probs_0_3.append(matrix.get((0, 3), 0))

df['Prob_0_1'] = probs_0_1
df['Prob_0_2'] = probs_0_2
df['Prob_0_3'] = probs_0_3

df['Power_0_1'] = (1 - df['Prob_0_1']) * 100
df['Power_0_2'] = (1 - df['Prob_0_2']) * 100
df['Power_0_3'] = (1 - df['Prob_0_3']) * 100

df['Result_0_1'] = ((df['homeGoalCount'] == 0) & (df['awayGoalCount'] == 1)).astype(int)
df['Result_0_2'] = ((df['homeGoalCount'] == 0) & (df['awayGoalCount'] == 2)).astype(int)
df['Result_0_3'] = ((df['homeGoalCount'] == 0) & (df['awayGoalCount'] == 3)).astype(int)

# Bins for Score Bands
bins = [0, 80, 85, 88, 90, 92, 94, 96, 98, 99, 100]
labels = ['0-80', '81-85', '86-88', '89-90', '91-92', '93-94', '95-96', '97-98', '99', '100']

def print_report(target_name, power_col, result_col, odd_estimada):
    print(f"\n==============================")
    print(f"RELATORIO LAY CS {target_name}")
    print(f"==============================")
    df['Band'] = pd.cut(df[power_col], bins=bins, labels=labels, right=True)
    
    for band in labels:
        sub = df[df['Band'] == band]
        t = len(sub)
        if t == 0: continue
        
        losses = sub[result_col].sum() # Perdeu no CS Lay (o resultado foi EXATAMENTE esse)
        wins = t - losses # Ganhou no CS Lay (foi qualquer outro placar)
        win_rate = wins / t
        
        lucro_bruto = wins * 100
        prejuizo = losses * 100 * (odd_estimada - 1)
        lucro_liquido = lucro_bruto - prejuizo
        roi = (lucro_liquido / (t*100)) * 100
        
        print(f"Score: {band:<6} | Vol: {t:<5} | Wr: {win_rate*100:5.2f}% | Lucro Est (Odd {odd_estimada}): R$ {lucro_liquido:8.2f} | ROI: {roi:5.2f}%")

print_report("0 a 1", "Power_0_1", "Result_0_1", 12.0)
print_report("0 a 2", "Power_0_2", "Result_0_2", 15.0)
print_report("0 a 3", "Power_0_3", "Result_0_3", 30.0)
