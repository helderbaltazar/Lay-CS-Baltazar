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

# Regra 1 e Regra 2
df['Soma_Media_HT'] = df['Media_Gols_no_1T_Casa'] + df['Media_Gols_no_1T_Visitante']
df['U05'] = (df['HTGoalCount'] < 0.5).astype(int)

# Golden Filter
mask = (df['Soma_Media_HT'] <= 1.2) & \
       (df['Efic_xG_Casa'] <= 1.0) & \
       (df['Efic_xG_Visitante'] <= 1.0) & \
       (df['Efic_xG_Casa'] > 0) & \
       (df['Efic_xG_Visitante'] > 0) & \
       (df['odds_1st_half_under05'] >= 2.70)

golden_df = df[mask].copy()

# Calculate Power Score
model = PoissonDixonColes(rho=-0.10)
power_scores = []
for idx, row in golden_df.iterrows():
    lam_home = float(row.get('Media_Gols_Total_Casa', 0) or 0)
    lam_away = float(row.get('Media_Gols_Total_Visitante', 0) or 0)
    
    if lam_home == 0 and lam_away == 0:
        power_scores.append(0)
    else:
        probs = model.get_extra_probabilities(lam_home, lam_away)
        power_scores.append(probs["UNDER_0.5_HT"] * 100)

golden_df['Power_Score'] = power_scores

# Create Power Score Bands
bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
labels = ['0-10', '11-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '81-90', '91-100']
golden_df['Score_Band'] = pd.cut(golden_df['Power_Score'], bins=bins, labels=labels, right=True)

print("=== DISTRIBUIÇÃO DO POWER SCORE (Filtro de Ouro Under 0.5 HT) ===")
print("Total de Jogos no Filtro:", len(golden_df))

for band in labels:
    sub = golden_df[golden_df['Score_Band'] == band]
    t = len(sub)
    if t == 0: continue
    
    h = sub['U05'].sum()
    wr = h / t
    inv = t * 100
    ret = (sub[sub['U05'] == 1]['odds_1st_half_under05'] * 100).sum()
    lucro = ret - inv
    roi = (lucro / inv) * 100
    
    print(f"\nPower Score: {band}")
    print(f"  Volume: {t} jogos | Acertos: {h} | Win Rate: {wr*100:.2f}%")
    print(f"  Lucro: R$ {lucro:.2f} | ROI: {roi:.2f}%")
