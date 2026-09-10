import sqlite3
import pandas as pd
from models.poisson import PoissonDixonColes

conn = sqlite3.connect("data_store/database.sqlite3")
df = pd.read_sql_query("""
    SELECT 
        homeGoalCount, awayGoalCount, totalGoalCount,
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante,
        Media_Gols_no_1T_Casa, Media_Gols_no_1T_Visitante,
        Efic_xG_Casa, Efic_xG_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_Total_Casa IS NOT NULL 
""", conn)
conn.close()

model = PoissonDixonColes()
cache = {}
p_u25 = []
for idx, row in df.iterrows():
    h = row["Media_Gols_Total_Casa"]
    a = row["Media_Gols_Total_Visitante"]
    key = (h, a)
    if key not in cache:
        cache[key] = model.predict(h if h > 0 else 0.1, a if a > 0 else 0.1)
    p_u25.append(sum(cache[key].get((hg, ag), 0) for hg in range(3) for ag in range(3) if hg+ag <= 2))

df["Power_U25"] = p_u25
df['Soma_HT'] = df['Media_Gols_no_1T_Casa'] + df['Media_Gols_no_1T_Visitante']
df['U25_Hit'] = df['totalGoalCount'] <= 2

print("\n--- UNDER 2.5 FT EXTREME STUDY ---")
best_wr = 0
for min_p in [0.5, 0.6, 0.7, 0.8]:
    for max_soma_ht in [0.8, 1.0, 1.2]:
        for max_efic in [0.5, 0.7, 0.8, 1.0]:
            mask = (df['Power_U25'] >= min_p) & (df['Soma_HT'] <= max_soma_ht) & (df['Efic_xG_Casa'] <= max_efic) & (df['Efic_xG_Visitante'] <= max_efic)
            sub = df[mask]
            vol = len(sub)
            if vol < 100: continue
            
            wr = sub['U25_Hit'].mean()
            if wr > best_wr:
                best_wr = wr
                print(f"New Best: Power>{min_p*100:.0f}%, SomaHT<={max_soma_ht}, Efic<={max_efic} -> WR: {wr*100:.2f}% | Vol: {vol}")

