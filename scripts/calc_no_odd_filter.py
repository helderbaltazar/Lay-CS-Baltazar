import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.poisson import PoissonDixonColes

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        HTGoalCount, odds_1st_half_under05,
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante,
        Media_Gols_no_1T_Casa, Media_Gols_no_1T_Visitante,
        Efic_xG_Casa, Efic_xG_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_no_1T_Casa IS NOT NULL 
      AND HTGoalCount IS NOT NULL
      AND odds_1st_half_under05 IS NOT NULL
      AND Efic_xG_Casa IS NOT NULL
      AND Efic_xG_Visitante IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

df['Soma_Media_HT'] = df['Media_Gols_no_1T_Casa'] + df['Media_Gols_no_1T_Visitante']
df['U05'] = (df['HTGoalCount'] < 0.5).astype(int)
df = df[df['odds_1st_half_under05'] > 1.0].copy()

# Calculate Power Score
model = PoissonDixonColes(rho=-0.10)
power_scores = []
for idx, row in df.iterrows():
    lam_home = float(row.get('Media_Gols_Total_Casa', 0) or 0)
    lam_away = float(row.get('Media_Gols_Total_Visitante', 0) or 0)
    if lam_home == 0 and lam_away == 0:
        power_scores.append(0)
    else:
        probs = model.get_extra_probabilities(lam_home, lam_away)
        power_scores.append(probs["UNDER_0.5_HT"] * 100)

df['Power_Score'] = power_scores

def print_report(name, mask):
    sub = df[mask]
    t = len(sub)
    if t == 0:
        print(f"\n{name}: 0 jogos")
        return
    h = sub['U05'].sum()
    wr = h / t
    inv = t * 100
    ret = (sub[sub['U05'] == 1]['odds_1st_half_under05'] * 100).sum()
    lucro = ret - inv
    roi = (lucro / inv) * 100
    odd_media = sub[sub['U05'] == 1]['odds_1st_half_under05'].mean()
    
    print(f"\n=== {name} ===")
    print(f"Volume: {t} jogos | Acertos: {h}")
    print(f"Win Rate: {wr*100:.2f}%")
    print(f"Odd Média dos Acertos: {odd_media:.2f}")
    print(f"Financeiro: Investido R$ {inv:.2f} | Retorno R$ {ret:.2f}")
    print(f"Lucro/Prejuízo: R$ {lucro:.2f} | ROI: {roi:.2f}%")

# 3. SEM O FILTRO DA ODD
mask_no_odd = (df['Power_Score'] >= 30) & \
              (df['Soma_Media_HT'] <= 1.2) & \
              (df['Efic_xG_Casa'] <= 1.0) & \
              (df['Efic_xG_Visitante'] <= 1.0) & \
              (df['Efic_xG_Casa'] > 0) & \
              (df['Efic_xG_Visitante'] > 0)

print_report("3. POWER SCORE + SOMA_HT + EFIC_XG (SEM EXIGIR ODD MÍNIMA)", mask_no_odd)

