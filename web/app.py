from flask import Flask, render_template, request
from database.db import SessionLocal
from database.models_db import Match, Prediction
import datetime
import config
from sqlalchemy import desc, func

app = Flask(__name__)

@app.route("/")
def index():
    db = SessionLocal()
    import pytz
    today = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE)).strftime("%Y-%m-%d")
    date_filter = request.args.get('date', today)
    
    try:
        date_obj = datetime.datetime.strptime(date_filter, "%Y-%m-%d").date()
    except:
        date_obj = datetime.datetime.strptime(today, "%Y-%m-%d").date()
        
    matches = db.query(Match).filter(func.date(Match.date) == date_obj).all()
    
    rankings = {t: [] for t in config.TARGET_SCORES}
    
    for m in matches:
        for p in m.predictions:
            if p.target_score in rankings:
                rankings[p.target_score].append({
                    'rank': p.rank,
                    'home': m.home_team,
                    'away': m.away_team,
                    'league': m.league_name,
                    'status': m.status,
                    'real_score': m.real_score,
                    'probability': p.probability
                })
                
    for t in config.TARGET_SCORES:
        rankings[t].sort(key=lambda x: x['rank'] or 9999)
        
    db.close()
    return render_template("index.html", rankings=rankings, date_filter=date_obj.strftime("%Y-%m-%d"))

@app.route("/history")
def history():
    db = SessionLocal()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    stats = {}
    for t in config.TARGET_SCORES:
        total = db.query(Prediction).join(Match).filter(Prediction.target_score == t, Match.status == 'FT').count()
        hits = db.query(Prediction).join(Match).filter(Prediction.target_score == t, Match.status == 'FT', Prediction.is_hit == True).count()
        rate = (hits / total * 100) if total > 0 else 0
        stats[t] = {'total': total, 'hits': hits, 'rate': round(rate, 1)}
        
    query = db.query(Prediction, Match).join(Match).filter(Match.status == 'FT').order_by(desc(Match.date))
    total_items = query.count()
    total_pages = (total_items + per_page - 1) // per_page
    
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    
    history_data = []
    for p, m in items:
        history_data.append({
            'date': m.date.strftime("%d/%m/%Y"),
            'league': m.league_name,
            'match': f"{m.home_team} x {m.away_team}",
            'target': p.target_score,
            'prob': f"{p.probability*100:.1f}%",
            'real_score': m.real_score,
            'is_hit': p.is_hit
        })
        
    db.close()
    return render_template("history.html", stats=stats, history=history_data, page=page, total_pages=total_pages)
