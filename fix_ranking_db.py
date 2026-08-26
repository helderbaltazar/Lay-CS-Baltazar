from database.db import SessionLocal
from database.models_db import Match, Prediction

db = SessionLocal()
# Deleta mocks residuais de testes passados que vazaram no DB
mock_matches = db.query(Match).filter(Match.fixture_id < 1000).all()
for m in mock_matches:
    db.delete(m)
db.commit()
print("Jogos fantasmas de testes removidos do BD.")
db.close()
