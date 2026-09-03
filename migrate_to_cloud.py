import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models_db import Match, Prediction, Base
from database.db import engine as cloud_engine, SessionLocal as CloudSession

sqlite_engine = create_engine("sqlite:///data_store/database.sqlite3")
LocalSession = sessionmaker(bind=sqlite_engine)

local_db = LocalSession()
cloud_db = CloudSession()

print("Buscando dados do banco local (SQLite)...")
local_matches = local_db.query(Match).all()

print(f"Encontrados {len(local_matches)} jogos locais. Iniciando migração para a Nuvem...")

count = 0
for lm in local_matches:
    cm = cloud_db.query(Match).filter(Match.fixture_id == lm.fixture_id).first()
    if not cm:
        new_match = Match(
            fixture_id=lm.fixture_id,
            date=lm.date,
            league_name=lm.league_name,
            home_team=lm.home_team,
            away_team=lm.away_team,
            status=lm.status,
            real_score=lm.real_score
        )
        cloud_db.add(new_match)
        cloud_db.commit()
        cloud_db.refresh(new_match)
        
        for lp in lm.predictions:
            new_pred = Prediction(
                match_id=new_match.id,
                target_score=lp.target_score,
                probability=lp.probability,
                rank=lp.rank,
                is_hit=lp.is_hit
            )
            cloud_db.add(new_pred)
        cloud_db.commit()
        count += 1
    else:
        print(f"Jogo {lm.fixture_id} já existe na nuvem. Pulando.")

local_db.close()
cloud_db.close()
print(f"Migração concluída com sucesso! {count} novos jogos foram transferidos para o Supabase.")
