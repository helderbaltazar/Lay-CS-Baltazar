import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        HTGoalCount, odds_1st_half_under05,
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

# Filter Regra 1 and Regra 2
mask = (df['Soma_Media_HT'] <= 1.2) & \
       (df['Efic_xG_Casa'] <= 1.0) & \
       (df['Efic_xG_Visitante'] <= 1.0) & \
       (df['Efic_xG_Casa'] > 0) & \
       (df['Efic_xG_Visitante'] > 0) & \
       (df['odds_1st_half_under05'] > 1.0)

df_filtered = df[mask].copy()

# Create Odd Bands
bins = [1.0, 2.0, 2.3, 2.5, 2.7, 3.0, 3.5, 5.0, 100.0]
labels = ['1.01 - 2.00', '2.01 - 2.30', '2.31 - 2.50', '2.51 - 2.70', '2.71 - 3.00', '3.01 - 3.50', '3.51 - 5.00', '5.01+']
df_filtered['Odd_Band'] = pd.cut(df_filtered['odds_1st_half_under05'], bins=bins, labels=labels, right=True)

print("=== RESULTADOS POR FAIXA DE ODD (Stake R$ 100) ===")
print("Regras Aplicadas: Soma_Media_HT <= 1.2 AND Efic_xG (Ambos) <= 1.0\n")

for band in labels:
    sub = df_filtered[df_filtered['Odd_Band'] == band]
    t = len(sub)
    if t == 0: continue
    
    h = sub['U05'].sum()
    wr = h / t
    inv = t * 100
    ret = (sub[sub['U05'] == 1]['odds_1st_half_under05'] * 100).sum()
    lucro = ret - inv
    roi = (lucro / inv) * 100
    
    print(f"Faixa: {band}")
    print(f"  Apostas: {t} | Acertos: {h} | Win Rate: {wr*100:.2f}%")
    print(f"  Investido: R$ {inv:.2f} | Retorno: R$ {ret:.2f}")
    print(f"  Lucro: R$ {lucro:.2f} | ROI: {roi:.2f}%\n")
