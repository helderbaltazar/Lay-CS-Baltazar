import sqlite3
import pandas as pd
import sys
import os
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.poisson import PoissonDixonColes

def run_backtest():
    print("Iniciando Simulador de Monte Carlo (Backtest Histórico)...")
    
    conn = sqlite3.connect('data_store/database.sqlite3')
    
    # Vamos focar no mercado Under 2.5 como proxy para o Lay CS, 
    # já que temos as odds de Under 2.5 reais (Pinnacle/Bet365) no CSV.
    # O motor de Poisson continua sendo o mesmo.
    query = """
        SELECT MatchDate, HomeTeam, AwayTeam, FTHome, FTAway, 
               Under25, Over25, HomeTarget, AwayTarget
        FROM historical_dataset
        WHERE Under25 IS NOT NULL 
          AND HomeTarget IS NOT NULL 
          AND AwayTarget IS NOT NULL
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"Total de jogos válidos para backtest: {len(df)}")
    if len(df) == 0:
        return
        
    model = PoissonDixonColes()
    
    bankroll = 1000.0
    stake = 10.0 # Flat stake
    wins = 0
    losses = 0
    
    # Simplificação de média da liga: 1.40 home, 1.10 away
    avg_home = 1.40
    avg_away = 1.10
    
    history_pnl = []
    
    for index, row in df.iterrows():
        # Calcular xG sintético histórico usando chutes no alvo
        # (Ex: 30% de conversão do chute no alvo)
        sxg_home = row['HomeTarget'] * 0.30
        sxg_away = row['AwayTarget'] * 0.30
        
        # Para evitar zero division ou log(0)
        sxg_home = max(sxg_home, 0.1)
        sxg_away = max(sxg_away, 0.1)
        
        h_attack = sxg_home / avg_home
        a_attack = sxg_away / avg_away
        h_defense = sxg_home / avg_away  # Simplificado para backtest isolado
        a_defense = sxg_away / avg_home
        
        lam_home = h_attack * a_defense * avg_home
        lam_away = a_attack * h_defense * avg_away
        
        extra_probs = model.get_extra_probabilities(lam_home, lam_away)
        prob_under = extra_probs["UNDER_2.5"]
        
        odd_under = float(row['Under25'])
        
        # Filtro de valor esperado (EV > 5%)
        ev = (prob_under * odd_under) - 1.0
        
        if ev > 0.05:
            # Aposta efetuada
            total_goals = row['FTHome'] + row['FTAway']
            is_hit = total_goals < 2.5
            
            if is_hit:
                profit = stake * (odd_under - 1)
                bankroll += profit
                wins += 1
            else:
                bankroll -= stake
                losses += 1
                
            history_pnl.append(bankroll)

    total_bets = wins + losses
    if total_bets > 0:
        win_rate = wins / total_bets
        roi = ((bankroll - 1000.0) / (total_bets * stake)) * 100
        
        print("\n=== RESULTADOS DO BACKTEST ===")
        print(f"Apostas Realizadas: {total_bets}")
        print(f"Wins: {wins} | Losses: {losses}")
        print(f"Win Rate: {win_rate*100:.2f}%")
        print(f"Lucro Líquido: R$ {bankroll - 1000.0:.2f}")
        print(f"ROI: {roi:.2f}%")
    else:
        print("Nenhuma aposta com EV positivo encontrada no set.")

if __name__ == "__main__":
    run_backtest()
