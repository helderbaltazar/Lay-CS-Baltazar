import sqlite3
import pandas as pd
import numpy as np

def run_backtest():
    # Caminho do banco de dados (ajuste se necessário)
    db_path = 'data_store/database.sqlite3'
    
    try:
        from database.db import engine
        # Ler apenas jogos completos
        query = 'SELECT * FROM datafootball_historical WHERE "Status" = \'complete\' OR "Status" = \'finished\''
        df = pd.read_sql(query, engine)
    except Exception as e:
        print(f"Erro ao conectar ou ler o banco de dados: {e}")
        return
    
    if df.empty:
        print("A tabela datafootball_historical está vazia ou não tem jogos completos.")
        return

    # Limpeza e conversão das colunas de gols
    df['Gols HT Casa'] = pd.to_numeric(df.get('Gols HT Casa', df.get('team_a_fh_goals', 0)), errors='coerce').fillna(0)
    df['Gols HT Fora'] = pd.to_numeric(df.get('Gols HT Fora', df.get('team_b_fh_goals', 0)), errors='coerce').fillna(0)
    df['Total Gols HT'] = df['Gols HT Casa'] + df['Gols HT Fora']
    
    # O FT Goals geralmente vem na coluna 'Total Gols' ou 'Gols Totais'
    df['Total Gols FT'] = pd.to_numeric(df['Gols Casa'], errors='coerce').fillna(0) + pd.to_numeric(df['Gols Fora'], errors='coerce').fillna(0)

    # Converter odds e stats para numérico
    cols_to_convert = [
        'odds_1st_half_under05', 'odds_1st_half_under15', 'odds_1st_half_under25',
        'Under 2.5', 'Under 3.5', 'Under 4.5', 'Odd 1', 'Odd X', 'Odd 2',
        'total_xg_prematch', 'team_a_xg_prematch', 'team_b_xg_prematch'
    ]
    for col in cols_to_convert:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Criar total_xg_prematch caso não exista, mas existam os individuais
    if 'total_xg_prematch' not in df.columns and 'team_a_xg_prematch' in df.columns:
        df['total_xg_prematch'] = df['team_a_xg_prematch'] + df['team_b_xg_prematch']

    # Função auxiliar para testar e calcular métricas da estratégia
    def test_strategy(market_col, goal_col, limit, mask, name):
        if market_col not in df.columns or goal_col not in df.columns:
            return None
        
        filtered = df[mask].dropna(subset=[market_col, goal_col])
        if len(filtered) < 50: # Exige volume mínimo de 50 jogos
            return None
            
        hits = filtered[goal_col] < limit
        win_rate = hits.mean()
        
        # Calcular ROI
        # Lucro = Odd - 1 (em caso de green), -1 (em caso de red)
        odds = filtered[market_col]
        profits = np.where(hits, odds - 1, -1)
        roi = profits.mean() * 100
        
        return {
            'Mercado': name,
            'Jogos Filtrados': len(filtered),
            'Taxa de Acerto (%)': round(win_rate * 100, 2),
            'ROI Estimado (%)': round(roi, 2),
            'Odd Média': round(odds.mean(), 2)
        }

    results = []

    # 1. Filtros para Under 0.5 HT
    # Hipótese: Jogos sem super favoritos (odds > 2.0 para ambos) e expectativa de gols (xG) baixa (< 2.5)
    if 'total_xg_prematch' in df.columns:
        m1 = (df['total_xg_prematch'] < 2.5) & (df['Odd 1'] > 2.0) & (df['Odd 2'] > 2.0)
        results.append(test_strategy('odds_1st_half_under05', 'Total Gols HT', 0.5, m1, 'Under 0.5 HT (Low xG + Jogo Parelho)'))

    # 2. Filtros para Under 1.5 HT
    # Hipótese: Odd mínima de 1.25 para buscar valor, e xG total < 2.8
    if 'total_xg_prematch' in df.columns:
        m2 = (df['total_xg_prematch'] < 2.8) & (df['odds_1st_half_under15'] >= 1.25)
        results.append(test_strategy('odds_1st_half_under15', 'Total Gols HT', 1.5, m2, 'Under 1.5 HT (xG < 2.8 + Odd >= 1.25)'))

    # 3. Filtros para Under 2.5 HT
    # Hipótese: Para Under 2.5 HT as odds são muito esmagadas. Buscamos odd >= 1.05 em jogos sem super favorito.
    m3 = (df['odds_1st_half_under25'] >= 1.05) & (df['Odd 1'] > 1.5) & (df['Odd 2'] > 1.5)
    results.append(test_strategy('odds_1st_half_under25', 'Total Gols HT', 2.5, m3, 'Under 2.5 HT (Sem Super Favorito + Odd>=1.05)'))

    # 4. Filtros para Under 2.5 FT
    # Hipótese: Total xG < 2.2 e Odds de Under 2.5 pagando pelo menos 1.60
    if 'total_xg_prematch' in df.columns:
        m4 = (df['total_xg_prematch'] < 2.2) & (df['Under 2.5'] >= 1.60)
        results.append(test_strategy('Under 2.5', 'Total Gols FT', 2.5, m4, 'Under 2.5 FT (Low xG < 2.2 + Odd >= 1.60)'))

    # 5. Filtros para Under 3.5 FT
    # Hipótese: Evitar jogos com tendência de goleada limitando xG < 3.0 e buscando odd de Under justa (1.20 a 1.45)
    if 'total_xg_prematch' in df.columns:
        m5 = (df['total_xg_prematch'] < 3.0) & (df['Under 3.5'] >= 1.20) & (df['Under 3.5'] <= 1.45)
        results.append(test_strategy('Under 3.5', 'Total Gols FT', 3.5, m5, 'Under 3.5 FT (Odd Valor 1.20-1.45)'))

    # 6. Filtros para Under 4.5 FT
    # Hipótese: Garantia quase máxima. Odd mínima de 1.08 e evitar jogos com favoritos esmagadores (Odd 1 e Odd 2 > 1.8)
    m6 = (df['Under 4.5'] >= 1.08) & (df['Odd 1'] > 1.8) & (df['Odd 2'] > 1.8)
    results.append(test_strategy('Under 4.5', 'Total Gols FT', 4.5, m6, 'Under 4.5 FT (Jogo Parelho + Odd >= 1.08)'))

    # Mostrar Resultados
    res_df = pd.DataFrame([r for r in results if r is not None])
    print("\n" + "="*60)
    print(" RELATÓRIO DE BACKTEST (UNDER MARKETS - LAY CS) ")
    print("="*60)
    if not res_df.empty:
        # Formatar a saída
        print(res_df.to_string(index=False))
        print("="*60)
        print("NOTA: O ROI acima de 0% indica lucratividade histórica.")
    else:
        print("Nenhum dado válido com volume suficiente (>50 jogos) encontrado para as regras.")

if __name__ == '__main__':
    run_backtest()
