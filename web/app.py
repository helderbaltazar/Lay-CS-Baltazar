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
                    'probability': p.probability,
                    'is_hit': p.is_hit
                })
                
    for t in config.TARGET_SCORES:
        rankings[t].sort(key=lambda x: x['rank'] or 9999)
        
    db.close()
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today_str = now_br.strftime("%Y-%m-%d")
    tomorrow_str = (now_br + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    return render_template("index.html", rankings=rankings, date_filter=date_obj.strftime("%Y-%m-%d"), today_str=today_str, tomorrow_str=tomorrow_str)

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

@app.route("/analytics")
def analytics():
    db = SessionLocal()
    try:
        from sqlalchemy import func, case
        # Agrupa por liga para pegar total de jogos e win rate
        stats = db.query(
            Match.league_name,
            func.count(Match.id).label('total_games'),
            func.sum(
                case((Prediction.is_hit == True, 1), else_=0)
            ).label('hits'),
            func.sum(
                case((Prediction.is_hit == False, 1), else_=0)
            ).label('misses')
        ).join(Prediction).filter(
            Match.status.in_(['FT', 'AET', 'PEN']),
            Prediction.is_hit != None
        ).group_by(Match.league_name).all()
        
        analytics_data = []
        for s in stats:
            total = s.hits + s.misses
            win_rate = (s.hits / total * 100) if total > 0 else 0
            analytics_data.append({
                'league': s.league_name,
                'total': total,
                'hits': s.hits,
                'misses': s.misses,
                'win_rate': round(win_rate, 2)
            })
            
        # Ordena pelo melhor win rate
        analytics_data.sort(key=lambda x: x['win_rate'], reverse=True)
        return render_template("analytics.html", stats=analytics_data)
    finally:
        db.close()

@app.route("/export")
def export_csv():
    import csv
    from io import StringIO
    from flask import Response
    
    db = SessionLocal()
    try:
        matches = db.query(Match).join(Prediction).filter(
            Match.status.in_(['FT', 'AET', 'PEN'])
        ).order_by(Match.date.desc()).all()
        
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['Data', 'Liga', 'Casa', 'Visitante', 'Placar Real', 'Estrategia', 'Odd', 'Resultado'])
        
        for m in matches:
            for p in m.predictions:
                resultado = "GREEN" if p.is_hit else "RED" if p.is_hit == False else "PENDENTE"
                cw.writerow([
                    m.date.strftime("%Y-%m-%d"), m.league_name, m.home_team, m.away_team, 
                    m.real_score, p.target_score, "N/A", resultado
                ])
                
        output = si.getvalue()
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=historico_apostas.csv"}
        )
    finally:
        db.close()
