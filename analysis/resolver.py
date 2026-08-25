from database.db import SessionLocal
from database.models_db import Match, Prediction
from data.api_football import get_fixtures
from data import cache
import datetime

def resolve_pending_matches(date_str):
    db = SessionLocal()
    try:
        start_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        
        pending_matches = db.query(Match).filter(
            Match.status != 'FT',
            Match.status != 'AWD',
            Match.status != 'CANC',
            Match.status != 'PSTP'
        ).all()
        
        pending_matches = [m for m in pending_matches if m.date.date() == start_date]

        if not pending_matches:
            return 0
            
        real_fixtures = get_fixtures(date_str)
        real_dict = {f['fixture']['id']: f for f in real_fixtures}
        
        resolved_count = 0
        for m in pending_matches:
            api_data = real_dict.get(m.fixture_id)
            if api_data:
                status = api_data['fixture']['status']['short']
                m.status = status
                
                if status == 'FT':
                    goals_home = api_data['goals']['home']
                    goals_away = api_data['goals']['away']
                    if goals_home is not None and goals_away is not None:
                        real_score = f"{goals_home}-{goals_away}"
                        m.real_score = real_score
                        
                        cache.invalidate(f"stats_{api_data['teams']['home']['id']}_{api_data['league']['id']}")
                        cache.invalidate(f"stats_{api_data['teams']['away']['id']}_{api_data['league']['id']}")
                        
                        for pred in m.predictions:
                            pred.is_hit = (real_score != pred.target_score)
                        resolved_count += 1
                        
        db.commit()
        return resolved_count
    finally:
        db.close()
