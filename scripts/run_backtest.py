import os
import sys
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import SessionLocal
from database.models_db import Match, Prediction
from analysis.scanner import calculate_lambdas, scan_match
from models.poisson import PoissonDixonColes
import config

def run_backtest_for_league(league_name):
    """
    Roda o simulador de backtest para as partidas de uma liga no banco que não têm predições.
    Isso simula o scanner rodando no passado e gravando o hit/miss.
    """
    db = SessionLocal()
    print(f"Iniciando backtest para a liga: {league_name}")
    
    try:
        # Busca partidas sem predições (ou seja, inseridas pelo backtest)
        matches = db.query(Match).filter(
            Match.league_name == league_name,
            ~Match.predictions.any()
        ).all()
        
        if not matches:
            print("Nenhuma partida encontrada ou todas já possuem predições.")
            return

        model = PoissonDixonColes(rho=config.DIXON_COLES_RHO, max_goals=config.MAX_GOALS)
        count = 0
        
        for m in matches:
            # Aqui simulamos os lambdas (em um ambiente real, você buscaria do cache)
            # Para o backtest inicial, usaremos valores genéricos se não houver histórico
            home_stats = {'goalsFor': {'home': 1.5}, 'goalsAgainst': {'home': 1.0}}
            away_stats = {'goalsFor': {'away': 1.2}, 'goalsAgainst': {'away': 1.4}}
            league_avg = (1.4, 1.1)
            
            lam_home, lam_away = calculate_lambdas(home_stats, away_stats, league_avg)
            
            # Simulando os targets e predições
            # Em vez de fixture real, passamos um mock
            fixture_mock = {
                'fixture': {'id': m.fixture_id},
                'teams': {'home': {'name': m.home_team}, 'away': {'name': m.away_team}},
                'league': {'name': m.league_name}
            }
            
            results = scan_match(fixture_mock, model, config.TARGET_SCORES)
            
            # Salvar predições
            for tgt, prob in results['probabilities'].items():
                is_hit = (tgt != m.real_score) if m.real_score else None
                pred = Prediction(
                    match_id=m.id,
                    target_score=tgt,
                    probability=prob,
                    rank=0, # O rank precisaria ser recalculado por rodada, deixaremos 0 no mock
                    is_hit=is_hit
                )
                db.add(pred)
                
            count += 1
            if count % 100 == 0:
                db.commit()
                print(f"Processadas {count} partidas...")
                
        db.commit()
        print(f"Backtest concluído! {count} partidas analisadas.")
        
    except Exception as e:
        print(f"Erro no backtest: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executar backtest para partidas históricas")
    parser.add_argument("--league", help="Nome da liga para processar", required=True)
    
    args = parser.parse_args()
    if args.league:
        run_backtest_for_league(args.league)
