import sqlite3
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.poisson import PoissonDixonColes

def run_backtest():
    print("Iniciando Simulador de Mercados Alternativos (Backtest Histórico)...")
    
    conn = sqlite3.connect('data_store/database.sqlite3')
    
    query = """
        SELECT MatchDate, HomeTeam, AwayTeam, FTHome, FTAway, HTHome, HTAway,
               Under25, Over25, HomeTarget, AwayTarget
        FROM historical_dataset
        WHERE HomeTarget IS NOT NULL 
          AND AwayTarget IS NOT NULL
          AND HTHome IS NOT NULL
          AND HTAway IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Total de jogos válidos para backtest (com dados de HT): {len(df)}")
    
    model = PoissonDixonColes(rho=-0.10)
    
    results = {
        "UNDER_0.5_HT": [],
        "UNDER_1.5_HT": [],
        "UNDER_2.5_HT": [],
        "OVER_1.5": [],
        "OVER_2.5": [],
        "UNDER_2.5": [],
        "OVER_3.5": [],
        "UNDER_3.5": [],
        "UNDER_4.5": [],
        "BTTS_YES": [],
        "BTTS_NO": []
    }
    
    for idx, row in df.iterrows():
        fth = int(row['FTHome'])
        fta = int(row['FTAway'])
        hth = int(row['HTHome'])
        hta = int(row['HTAway'])
        
        total_goals = fth + fta
        total_goals_ht = hth + hta
        btts = 1 if (fth > 0 and fta > 0) else 0
        btts_no = 1 if btts == 0 else 0
        
        home_target = float(row['HomeTarget'])
        away_target = float(row['AwayTarget'])
        
        probs = model.get_extra_probabilities(home_target, away_target)
        
        results["UNDER_0.5_HT"].append({"score": probs.get("UNDER_0.5_HT", 0) * 100, "hit": 1 if total_goals_ht < 0.5 else 0})
        results["UNDER_1.5_HT"].append({"score": probs.get("UNDER_1.5_HT", 0) * 100, "hit": 1 if total_goals_ht < 1.5 else 0})
        results["UNDER_2.5_HT"].append({"score": probs.get("UNDER_2.5_HT", 0) * 100, "hit": 1 if total_goals_ht < 2.5 else 0})
        
        results["OVER_1.5"].append({"score": probs.get("OVER_1.5", 0) * 100, "hit": 1 if total_goals > 1.5 else 0})
        results["OVER_2.5"].append({"score": probs.get("OVER_2.5", 0) * 100, "hit": 1 if total_goals > 2.5 else 0})
        results["OVER_3.5"].append({"score": probs.get("OVER_3.5", 0) * 100, "hit": 1 if total_goals > 3.5 else 0})
        
        results["UNDER_2.5"].append({"score": probs.get("UNDER_2.5", 0) * 100, "hit": 1 if total_goals < 2.5 else 0})
        results["UNDER_3.5"].append({"score": probs.get("UNDER_3.5", 0) * 100, "hit": 1 if total_goals < 3.5 else 0})
        results["UNDER_4.5"].append({"score": probs.get("UNDER_4.5", 0) * 100, "hit": 1 if total_goals < 4.5 else 0})
        
        results["BTTS_YES"].append({"score": probs.get("BTTS_YES", 0) * 100, "hit": btts})
        results["BTTS_NO"].append({"score": probs.get("BTTS_NO", 0) * 100, "hit": btts_no})
        
        if idx > 0 and idx % 10000 == 0:
            print(f"Processado {idx} jogos...")
            
    print("\n--- RESULTADOS DO BACKTEST (WIN RATE) ---")
    thresholds = [70, 75, 80, 85, 90, 95]
    
    for market, data in results.items():
        print(f"\n📊 Mercado: {market}")
        for t in thresholds:
            bets = [d for d in data if d["score"] >= t]
            if not bets:
                continue
            hits = sum([d["hit"] for d in bets])
            win_rate = hits / len(bets) * 100
            fair_odd = 100 / win_rate if win_rate > 0 else 0
            
            print(f"  Nota >= {t}: Win Rate: {win_rate:.2f}% (Acertos: {hits}/{len(bets)}) | Odd Justa: {fair_odd:.2f}")

if __name__ == "__main__":
    run_backtest()
