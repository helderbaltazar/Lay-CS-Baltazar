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
p_u25, p_u35, p_u45 = [], [], []

for idx, row in df.iterrows():
    h = row["Media_Gols_Total_Casa"]
    a = row["Media_Gols_Total_Visitante"]
    key = (h, a)
    if key not in cache:
        h_eff = h if h > 0 else 0.1
        a_eff = a if a > 0 else 0.1
        cache[key] = model.predict(h_eff, a_eff)
    
    matrix = cache[key]
    u25 = sum(matrix.get((hg, ag), 0) for hg in range(3) for ag in range(3) if hg+ag <= 2)
    u35 = sum(matrix.get((hg, ag), 0) for hg in range(4) for ag in range(4) if hg+ag <= 3)
    u45 = sum(matrix.get((hg, ag), 0) for hg in range(5) for ag in range(5) if hg+ag <= 4)
    
    p_u25.append(u25)
    p_u35.append(u35)
    p_u45.append(u45)

df["Power_U25"] = p_u25
df["Power_U35"] = p_u35
df["Power_U45"] = p_u45
df['Soma_HT'] = df['Media_Gols_no_1T_Casa'] + df['Media_Gols_no_1T_Visitante']

df['U25_Hit'] = df['totalGoalCount'] <= 2
df['U35_Hit'] = df['totalGoalCount'] <= 3
df['U45_Hit'] = df['totalGoalCount'] <= 4

def evaluate_advanced(market_name, hit_col, power_col, est_odd):
    print(f"\n--- {market_name} (Est Odd: {est_odd:.2f}) ---")
    best_roi = -9999
    best_params = {}
    
    for min_p in [0.5, 0.6, 0.7, 0.8]:
        for max_soma_ht in [1.2, 1.4, 1.8, 2.5]:
            for max_efic in [0.8, 1.0, 1.5, 2.0]:
                mask = (df[power_col] >= min_p) & (df['Soma_HT'] <= max_soma_ht) & (df['Efic_xG_Casa'] <= max_efic) & (df['Efic_xG_Visitante'] <= max_efic)
                sub = df[mask]
                vol = len(sub)
                if vol < 150: continue
                
                wr = sub[hit_col].mean()
                profit = (sub[hit_col].sum() * 100 * (est_odd - 1)) - ((vol - sub[hit_col].sum()) * 100)
                roi = profit / (vol * 100)
                
                if roi > best_roi:
                    best_roi = roi
                    best_params = {'power': min_p, 'soma_ht': max_soma_ht, 'efic': max_efic, 'vol': vol, 'wr': wr, 'roi': roi, 'profit': profit}
                    
    if best_roi != -9999:
        print(f"Best: Power>{best_params['power']*100:.0f}%, SomaHT<={best_params['soma_ht']}, Efic<={best_params['efic']} -> WR: {best_params['wr']*100:.2f}% | Vol: {best_params['vol']} | ROI: {best_params['roi']*100:.2f}% | Profit: R$ {best_params['profit']:.2f}")

evaluate_advanced("UNDER 2.5 FT", "U25_Hit", "Power_U25", 1.60)
evaluate_advanced("UNDER 3.5 FT", "U35_Hit", "Power_U35", 1.30)
evaluate_advanced("UNDER 4.5 FT", "U45_Hit", "Power_U45", 1.15)

