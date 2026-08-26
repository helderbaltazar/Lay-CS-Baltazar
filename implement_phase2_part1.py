import os
import re

# 1. Update web/app.py with Analytics and Export routes
with open('web/app.py', 'r') as f:
    app_content = f.read()

new_routes = """
@app.route("/analytics")
def analytics():
    db = SessionLocal()
    try:
        from sqlalchemy import func
        # Agrupa por liga para pegar total de jogos e win rate
        stats = db.query(
            Match.league_name,
            func.count(Match.id).label('total_games'),
            func.sum(
                func.case((Prediction.is_hit == True, 1), else_=0)
            ).label('hits'),
            func.sum(
                func.case((Prediction.is_hit == False, 1), else_=0)
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
"""
if "@app.route(\"/analytics\")" not in app_content:
    app_content = app_content + new_routes
    with open('web/app.py', 'w') as f:
        f.write(app_content)
    print("Rotas de Analytics e Export adicionadas.")

# 2. Add Links to base.html and history.html
with open('web/templates/base.html', 'r') as f:
    base_html = f.read()
if "Analytics" not in base_html:
    base_html = base_html.replace(
        '<a href="/history" class="badge" style="background:#f1c40f; color:#000; text-decoration:none;">Histórico de Resultados</a>',
        '<a href="/history" class="badge" style="background:#f1c40f; color:#000; text-decoration:none;">Histórico</a>\n            <a href="/analytics" class="badge" style="background:#e84393; color:#fff; text-decoration:none;">Analytics</a>'
    )
    with open('web/templates/base.html', 'w') as f:
        f.write(base_html)

with open('web/templates/history.html', 'r') as f:
    hist_html = f.read()
if "/export" not in hist_html:
    hist_html = hist_html.replace(
        '<h2>Histórico de Resultados</h2>',
        '<div style="display: flex; justify-content: space-between; align-items: center;"><h2>Histórico de Resultados</h2><a href="/export" class="badge" style="background:#27ae60; color:#fff; text-decoration:none; padding:8px 15px;">📥 Exportar CSV</a></div>'
    )
    with open('web/templates/history.html', 'w') as f:
        f.write(hist_html)

# 3. Create analytics.html
analytics_template = """{% extends "base.html" %}
{% block content %}
<h2>Analytics de Desempenho por Liga</h2>
<div class="card">
    <table class="data-table">
        <thead>
            <tr>
                <th>Campeonato</th>
                <th>Total de Entradas</th>
                <th>Greens ✅</th>
                <th>Reds ❌</th>
                <th>Win Rate (%)</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for s in stats %}
            <tr>
                <td>{{ s.league }}</td>
                <td>{{ s.total }}</td>
                <td class="green">{{ s.hits }}</td>
                <td class="red">{{ s.misses }}</td>
                <td><strong>{{ s.win_rate }}%</strong></td>
                <td>
                    {% if s.total >= 10 and s.win_rate < 60.0 %}
                        <span class="badge" style="background:#e74c3c;">Blacklist</span>
                    {% elif s.total >= 10 and s.win_rate >= 80.0 %}
                        <span class="badge" style="background:#2ecc71;">Excelente</span>
                    {% else %}
                        <span class="badge" style="background:#95a5a6;">Análise</span>
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr><td colspan="6">Nenhum dado consolidado ainda.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}"""
with open('web/templates/analytics.html', 'w') as f:
    f.write(analytics_template)

# 4. Create analysis/blacklist.py
os.makedirs('analysis', exist_ok=True)
blacklist_code = """from sqlalchemy import func
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
"""
with open('analysis/blacklist.py', 'w') as f:
    f.write(blacklist_code)

print("Etapas Web Analytics, CSV e Blacklist injetadas com sucesso.")
