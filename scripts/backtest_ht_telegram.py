import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.poisson import PoissonDixonColes

# Connect to database
conn = sqlite3.connect('data_store/database.sqlite3')
query = """
    SELECT 
        Data_Hora_Jogo, home_name, away_name, 
        Media_Gols_Total_Casa, Media_Gols_Total_Visitante,
        HTGoalCount, odds_1st_half_under05
    FROM telegram_dataset
    WHERE Media_Gols_Total_Casa IS NOT NULL 
      AND Media_Gols_Total_Visitante IS NOT NULL
      AND HTGoalCount IS NOT NULL
"""
df = pd.read_sql_query(query, conn)
conn.close()

model = PoissonDixonColes(rho=-0.10)
print(f"Total de jogos analisados: {len(df)}")

results = {
    "UNDER_0.5_HT": {"matches": 0, "hits": 0, "invested": 0, "returned": 0},
    "UNDER_1.5_HT": {"matches": 0, "hits": 0},
    "UNDER_2.5_HT": {"matches": 0, "hits": 0}
}

# Define cutoffs (Notas de Corte)
cutoffs = {
    "UNDER_0.5_HT": 80, 
    "UNDER_1.5_HT": 90, 
    "UNDER_2.5_HT": 95
}

for idx, row in df.iterrows():
    # Only use matches where the team played a few games, but the dataset might already be filtered.
    lam_home = float(row['Media_Gols_Total_Casa'])
    lam_away = float(row['Media_Gols_Total_Visitante'])
    
    # Ignore weird/invalid lambdas (like 0 if the team never scored/played)
    if lam_home == 0 and lam_away == 0:
        continue
        
    probs = model.get_extra_probabilities(lam_home, lam_away)
    
    ht_goals = int(row['HTGoalCount'])
    
    # UNDER 0.5 HT
    score_05 = probs["UNDER_0.5_HT"] * 100
    if score_05 >= cutoffs["UNDER_0.5_HT"]:
        results["UNDER_0.5_HT"]["matches"] += 1
        if ht_goals < 0.5:
            results["UNDER_0.5_HT"]["hits"] += 1
            odd = row.get("odds_1st_half_under05")
            if pd.notna(odd) and float(odd) > 1.0:
                results["UNDER_0.5_HT"]["invested"] += 100
                results["UNDER_0.5_HT"]["returned"] += 100 * float(odd)
            else:
                # Se não tiver odd, conta o hit mas sem financeiro para não distorcer
                pass
        else:
            odd = row.get("odds_1st_half_under05")
            if pd.notna(odd) and float(odd) > 1.0:
                results["UNDER_0.5_HT"]["invested"] += 100

    # UNDER 1.5 HT
    score_15 = probs["UNDER_1.5_HT"] * 100
    if score_15 >= cutoffs["UNDER_1.5_HT"]:
        results["UNDER_1.5_HT"]["matches"] += 1
        if ht_goals < 1.5:
            results["UNDER_1.5_HT"]["hits"] += 1
            
    # UNDER 2.5 HT
    score_25 = probs["UNDER_2.5_HT"] * 100
    if score_25 >= cutoffs["UNDER_2.5_HT"]:
        results["UNDER_2.5_HT"]["matches"] += 1
        if ht_goals < 2.5:
            results["UNDER_2.5_HT"]["hits"] += 1

print("\n=== RESULTADOS DO BACKTEST (HT) ===")
for market in ["UNDER_0.5_HT", "UNDER_1.5_HT", "UNDER_2.5_HT"]:
    res = results[market]
    matches = res["matches"]
    hits = res["hits"]
    if matches > 0:
        wr = (hits / matches) * 100
        fair_odd = 100 / wr if wr > 0 else 0
        print(f"\n{market} (Nota >= {cutoffs[market]}):")
        print(f"Apostas: {matches} | Acertos: {hits} | Win Rate: {wr:.2f}% | Odd Justa: {fair_odd:.2f}")
        
        if market == "UNDER_0.5_HT" and res["invested"] > 0:
            inv = res["invested"]
            ret = res["returned"]
            profit = ret - inv
            roi = (profit / inv) * 100
            print(f"Financeiro (Odd Real Pinnacle): Investido R$ {inv:.2f} | Retorno R$ {ret:.2f} | Lucro R$ {profit:.2f} (ROI: {roi:.2f}%)")
    else:
        print(f"\n{market}: Nenhum jogo atendeu a nota de corte {cutoffs[market]}.")
