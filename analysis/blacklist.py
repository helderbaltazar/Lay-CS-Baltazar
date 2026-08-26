from sqlalchemy import func
from database.models_db import Match, Prediction

def get_blacklisted_leagues(db, min_games=10, min_win_rate=60.0):
    stats = db.query(
        Match.league_name,
        func.count(Match.id).label('total_games'),
        func.sum(func.case((Prediction.is_hit == True, 1), else_=0)).label('hits')
    ).join(Prediction).filter(
        Match.status.in_(['FT', 'AET', 'PEN']),
        Prediction.is_hit != None
    ).group_by(Match.league_name).all()
    
    blacklisted = []
    for s in stats:
        if s.total_games >= min_games:
            win_rate = (s.hits / s.total_games) * 100
            if win_rate < min_win_rate:
                blacklisted.append(s.league_name)
    return blacklisted
