import os

with open('web/app.py', 'r') as f:
    app_py = f.read()

import re

# Find the start of the analytics_data loop and the sort
start_idx = app_py.find("analytics_data = []")
end_idx = app_py.find("return render_template('analytics.html'", start_idx)

if start_idx != -1 and end_idx != -1:
    new_logic = """analytics_data = []
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
            
        analytics_data.sort(key=lambda x: x['win_rate'], reverse=True)
        
        # Calcula Win-Rate Top 5
        top5_stats = db.query(
            func.count(Match.id).label('total'),
            func.sum(case((Prediction.is_hit == True, 1), else_=0)).label('hits')
        ).join(Prediction).filter(
            Match.status.in_(['FT', 'AET', 'PEN']),
            Prediction.is_hit != None,
            Match.rank_position <= 5
        ).first()
        
        top5_total = top5_stats.total if top5_stats and top5_stats.total else 0
        top5_hits = top5_stats.hits if top5_stats and top5_stats.hits else 0
        top5_winrate = (top5_hits / top5_total * 100) if top5_total > 0 else 0.0

        # Calcula Win-Rate Confiança >= 95
        high_conf_stats = db.query(
            func.count(Match.id).label('total'),
            func.sum(case((Prediction.is_hit == True, 1), else_=0)).label('hits')
        ).join(Prediction).filter(
            Match.status.in_(['FT', 'AET', 'PEN']),
            Prediction.is_hit != None,
            Match.ai_confidence >= 95
        ).first()
        
        high_total = high_conf_stats.total if high_conf_stats and high_conf_stats.total else 0
        high_hits = high_conf_stats.hits if high_conf_stats and high_conf_stats.hits else 0
        high_winrate = (high_hits / high_total * 100) if high_total > 0 else 0.0
        
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
            chart_data.append(round(acc_profit, 2))
            
        """
    
    app_py = app_py[:start_idx] + new_logic + app_py[end_idx:]

with open('web/app.py', 'w') as f:
    f.write(app_py)
