from database.db import SessionLocal
from database.models_db import Match, Prediction

db = SessionLocal()
bad_preds = db.query(Prediction).filter(Prediction.rank == None).all()
for p in bad_preds:
    db.delete(p)
    
bad_matches = db.query(Match).filter(Match.fixture_id == 999).all()
for m in bad_matches:
    db.delete(m)
    
db.commit()
print('Dados corrompidos removidos com sucesso!')
db.close()
