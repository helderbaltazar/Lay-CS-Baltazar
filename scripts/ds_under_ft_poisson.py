import sqlite3
import pandas as pd
from models.poisson import PoissonDixonColes

# Load full DB
conn = sqlite3.connect("data_store/database.sqlite3")
df = pd.read_sql_query("""
    SELECT 
        homeGoalCount, awayGoalCount, totalGoalCount,
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante,
        Media_Gols_no_1T_Casa, Media_Gols_no_1T_Visitante,
        Efic_xG_Casa, Efic_xG_Visitante
    FROM telegram_dataset
    WHERE Media_Gols_Total_Casa IS NOT NULL 
      AND Media_Gols_Total_Visitante IS NOT NULL
      AND totalGoalCount IS NOT NULL
""", conn)
conn.close()

model = PoissonDixonColes()
cache = {}
p_u25, p_u35, p_u45 = [], [], []

print("Calculating Poisson Probabilities...")
for idx, row in df.iterrows():
    h = row["Media_Gols_Total_Casa"]
    a = row["Media_Gols_Total_Visitante"]
    key = (h, a)
    if key not in cache:
        h_eff = h if h > 0 else 0.1
        a_eff = a if a > 0 else 0.1
        cache[key] = model.predict(h_eff, a_eff)
    
    matrix = cache[key]
    
    # Under 2.5
    u25 = sum(matrix.get((hg, ag), 0) for hg in range(3) for ag in range(3) if hg+ag <= 2)
    # Under 3.5
    u35 = sum(matrix.get((hg, ag), 0) for hg in range(4) for ag in range(4) if hg+ag <= 3)
    # Under 4.5
    u45 = sum(matrix.get((hg, ag), 0) for hg in range(5) for ag in range(5) if hg+ag <= 4)
    
    p_u25.append(u25)
    p_u35.append(u35)
    p_u45.append(u45)

df["Power_U25"] = p_u25
df["Power_U35"] = p_u35
df["Power_U45"] = p_u45
df['Soma_Media_Gols_FT'] = df['Media_Gols_Total_Casa'] + df['Media_Gols_Total_Visitante']

df['U25_Hit'] = df['totalGoalCount'] <= 2
df['U35_Hit'] = df['totalGoalCount'] <= 3
df['U45_Hit'] = df['totalGoalCount'] <= 4

def evaluate_market(market_name, hit_col, power_col, est_odd):
    print(f"\n--- {market_name} (Est Odd: {est_odd:.2f}) ---")
    best_roi = -9999
    best_p = 0
    
    for min_p in [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]:
        mask = df[power_col] >= min_p
        sub = df[mask]
        vol = len(sub)
        if vol < 200: continue
        wr = sub[hit_col].mean()
        
        profit = (sub[hit_col].sum() * 100 * (est_odd - 1)) - ((vol - sub[hit_col].sum()) * 100)
        roi = profit / (vol * 100)
        
        if roi > best_roi:
            best_roi = roi
            best_p = min_p
            best_vol = vol
            best_wr = wr
            best_prof = profit
            
    print(f"Best: Power > {best_p*100:.1f} -> WR: {best_wr*100:.2f}% | Vol: {best_vol} | ROI: {best_roi*100:.2f}% | Profit: R$ {best_prof:.2f}")

evaluate_market("UNDER 2.5 FT", "U25_Hit", "Power_U25", 1.60)
evaluate_market("UNDER 3.5 FT", "U35_Hit", "Power_U35", 1.30)
evaluate_market("UNDER 4.5 FT", "U45_Hit", "Power_U45", 1.15)
