import os

with open('web/app.py', 'r') as f:
    app_py = f.read()

# Replace the api/analysis route
old_route = """@app.route('/api/analysis')
@auth.login_required
def api_deep_analysis():
    home = request.args.get('home', 'Mandante')
    away = request.args.get('away', 'Visitante')
    league = request.args.get('league', 'Desconhecida')
    from analysis.ai_analyst import AIAnalyst
    data = AIAnalyst.get_deep_match_analysis(home, away, league)
    from flask import jsonify
    return jsonify(data)"""

# I added another one later using echo >>
old_route_2 = """@app.route('/api/analysis')
def api_deep_analysis():
    from flask import request, jsonify
    home = request.args.get('home', 'Mandante')
    away = request.args.get('away', 'Visitante')
    league = request.args.get('league', 'Desconhecida')
    from analysis.ai_analyst import AIAnalyst
    data = AIAnalyst.get_deep_match_analysis(home, away, league)
    return jsonify(data)"""

new_route = """@app.route('/api/analysis')
def api_deep_analysis():
    from flask import request, jsonify
    home = request.args.get('home', 'Mandante')
    away = request.args.get('away', 'Visitante')
    league = request.args.get('league', 'Desconhecida')
    fixture_id = request.args.get('fixture_id')
    if fixture_id:
        fixture_id = int(fixture_id)
        
    from analysis.ai_analyst import AIAnalyst
    data = AIAnalyst.get_deep_match_analysis(home, away, league, fixture_id=fixture_id)
    return jsonify(data)"""

if old_route in app_py:
    app_py = app_py.replace(old_route, new_route)
if old_route_2 in app_py:
    app_py = app_py.replace(old_route_2, new_route)
    
# Now the analytics route
old_analytics = """        analytics_data = []
        for s in stats:
            total = s.hits + s.misses
            win_rate = (s.hits / total * 100) if total > 0 else 0
            profit = float(s.profit) if s.profit is not None else 0.0
            roi = (profit / total * 100) if total > 0 else 0.0
            
            analytics_data.append({
                'league': s.league_name,
                'total_games': total,
                'hits': s.hits,
                'misses': s.misses,
                'win_rate': round(win_rate, 2),
                'profit': round(profit, 2),
                'roi': round(roi, 2)
            })"""

new_analytics = """        analytics_data = []
        for s in stats:
            total = s.hits + s.misses
            win_rate = (s.hits / total * 100) if total > 0 else 0
            profit = float(s.profit) if s.profit is not None else 0.0
            roi = (profit / total * 100) if total > 0 else 0.0
            
            analytics_data.append({
                'league': s.league_name,
                'total_games': total,
                'hits': s.hits,
                'misses': s.misses,
                'win_rate': round(win_rate, 2),
                'profit': round(profit, 2),
                'roi': round(roi, 2)
            })
            
        # Calcula Win-Rate Top 5
        top5_stats = db.query(
            func.count(Match.id).label('total'),
            func.sum(case((Prediction.is_hit == True, 1), else_=0)).label('hits')
        ).join(Prediction).filter(
            Match.status.in_(['FT', 'AET', 'PEN']),
            Prediction.is_hit != None,
            Match.rank_position <= 5
        ).one()
        
        top5_total = top5_stats.total or 0
        top5_hits = top5_stats.hits or 0
        top5_winrate = (top5_hits / top5_total * 100) if top5_total > 0 else 0.0

        # Calcula Win-Rate Confiança >= 95
        high_conf_stats = db.query(
            func.count(Match.id).label('total'),
            func.sum(case((Prediction.is_hit == True, 1), else_=0)).label('hits')
        ).join(Prediction).filter(
            Match.status.in_(['FT', 'AET', 'PEN']),
            Prediction.is_hit != None,
            Match.ai_confidence >= 95
        ).one()
        
        high_total = high_conf_stats.total or 0
        high_hits = high_conf_stats.hits or 0
        high_winrate = (high_hits / high_total * 100) if high_total > 0 else 0.0
        
        # Dados para grafico de curva (lucro por data nos Top 5)
        # Assuming Match.date is a string or datetime
        curve_query = db.query(
            Match.date,
            func.sum(Prediction.profit_loss).label('daily_profit')
        ).join(Prediction).filter(
            Match.status.in_(['FT', 'AET', 'PEN']),
            Prediction.is_hit != None,
            Match.rank_position <= 5
        ).group_by(Match.date).order_by(Match.date).all()
        
        chart_labels = []
        chart_data = []
        acc_profit = 0.0
        for row in curve_query:
            chart_labels.append(str(row.date))
            acc_profit += float(row.daily_profit or 0.0)
            chart_data.append(round(acc_profit, 2))"""

if old_analytics in app_py:
    app_py = app_py.replace(old_analytics, new_analytics)
    
old_render = "return render_template('analytics.html', analytics_data=analytics_data)"
new_render = "return render_template('analytics.html', analytics_data=analytics_data, top5_winrate=round(top5_winrate, 2), high_winrate=round(high_winrate, 2), chart_labels=chart_labels, chart_data=chart_data)"
if old_render in app_py:
    app_py = app_py.replace(old_render, new_render)
    
with open('web/app.py', 'w') as f:
    f.write(app_py)
