from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import database.db
def get_session():
    return database.db.SessionLocal()
from database.models_db import Match, Prediction
import datetime
import config
import threading
from sqlalchemy import desc, func


app = Flask(__name__)
app.secret_key = 'laycs-secret-key-2026'

auth = HTTPBasicAuth()

users = {
    config.DASHBOARD_USERNAME: generate_password_hash(config.DASHBOARD_PASSWORD)
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None


# Variavel global para status da execucao
_task_status = {'running': False, 'message': '', 'last_run': None}

@app.route("/force-scan", methods=["POST"])
@auth.login_required
def force_scan():
    """Forca a execucao do scan completo remotamente via GitHub Actions."""
    global _task_status
    if not config.GITHUB_TOKEN:
        flash("❌ GITHUB_TOKEN não configurado. Não é possível disparar a Action.", "danger")
        return redirect(url_for('index'))
        
    import requests
    
    repo = "helderbaltazar/Lay-CS-Baltazar"
    url = f"https://api.github.com/repos/{repo}/actions/workflows/daily_injection.yml/dispatches"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {config.GITHUB_TOKEN}"
    }
    data = {"ref": "main"}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 204:
            flash("🚀 Robô acionado no GitHub com sucesso! Acompanhe o Telegram.", "success")
        else:
            flash(f"❌ Erro ao acionar robô: {response.status_code} - {response.text}", "danger")
    except Exception as e:
        flash(f"❌ Erro de conexão: {str(e)}", "danger")
        
    return redirect(url_for('index'))

@app.route("/force-inject", methods=["POST"])
def force_inject():
    """Forca apenas a injecao dos times nos bots Layback (sem re-scan)."""
    global _task_status
    if _task_status['running']:
        flash("⏳ Já existe uma tarefa em execução. Aguarde finalizar.", "warning")
        return redirect(url_for('index'))
    
    def _run_inject():
        global _task_status
        _task_status['running'] = True
        _task_status['message'] = 'Injetando times nos bots Layback...'
        try:
            _inject_teams_into_bots()
            import pytz
            now = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
            _task_status['message'] = f'✅ Injeção concluída com sucesso às {now.strftime("%H:%M:%S")}!'
            _task_status['last_run'] = now.strftime("%d/%m/%Y %H:%M:%S")
        except Exception as e:
            _task_status['message'] = f'❌ Erro: {str(e)}'
        finally:
            _task_status['running'] = False
    
    thread = threading.Thread(target=_run_inject, daemon=True)
    thread.start()
    flash("🤖 Injeção nos Bots Layback iniciada!", "success")
    return redirect(url_for('index'))

@app.route("/task-status")
def task_status():
    """Retorna o status da tarefa em execucao (para polling AJAX)."""
    return jsonify(_task_status)

def _inject_teams_into_bots():
    """Busca os melhores jogos do banco e injeta nos bots Layback via API."""
    import pytz
    from integration.layback import update_layback_bots
    
    db = get_session()
    try:
        now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
        today = now_br.strftime("%Y-%m-%d")
        tomorrow = (now_br + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Busca os melhores jogos (rank 1) para cada target score
        best_picks = {}
        for target in config.TARGET_SCORES:
            match = db.query(Match).join(Prediction).filter(
                Prediction.target_score == target,
                Prediction.rank == 1,
                func.date(Match.date).in_([today, tomorrow]),
                Match.status == 'NS'
            ).first()
            
            if match:
                best_picks[target] = match
                print(f"[Inject] Melhor jogo para Lay {target}: {match.home_team} x {match.away_team}")
            else:
                print(f"[Inject] Nenhum jogo encontrado para Lay {target}")
        
        if best_picks:
            update_layback_bots(best_picks)
        else:
            print("[Inject] Nenhum jogo para injetar nos bots.")
            from notifications.telegram import send_message
            send_message("⚠️ Nenhum jogo encontrado no scan de hoje/amanhã para injetar nos bots Layback.")
    finally:
        db.close()

@app.route("/")
@auth.login_required
def index():
    db = get_session()
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
                    'is_hit': p.is_hit,
                    'match_odd': p.match_odd,
                    'profit_loss': p.profit_loss,
                    'ai_verdict': p.ai_verdict or 'APROVADO',
                    'ai_confidence': p.ai_confidence or 85,
                    'ai_critical_factor': p.ai_critical_factor or '',
                    'ai_analysis': p.ai_analysis or ''
                })
                
    for t in config.TARGET_SCORES:
        rankings[t].sort(key=lambda x: x['rank'] or 9999)
        
    db.close()
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today_str = now_br.strftime("%Y-%m-%d")
    tomorrow_str = (now_br + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    return render_template("index.html", rankings=rankings, date_filter=date_obj.strftime("%Y-%m-%d"), today_str=today_str, tomorrow_str=tomorrow_str)

@app.route("/history")
@auth.login_required
def history():
    db = get_session()
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
@auth.login_required
def analytics():
    db = get_session()
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
            ).label('misses'),
            func.sum(Prediction.profit_loss).label('profit')
        ).join(Prediction).filter(
            Match.status.in_(['FT', 'AET', 'PEN']),
            Prediction.is_hit != None
        ).group_by(Match.league_name).all()
        
        analytics_data = []
        for s in stats:
            total = s.hits + s.misses
            win_rate = (s.hits / total * 100) if total > 0 else 0
            profit = float(s.profit) if s.profit is not None else 0.0
            roi = (profit / total * 100) if total > 0 else 0.0
            analytics_data.append({
                'league': s.league_name,
                'total': total,
                'hits': s.hits,
                'misses': s.misses,
                'win_rate': round(win_rate, 2),
                'profit': round(profit, 2),
                'roi': round(roi, 2)
            })
            
        # Ordena pelo melhor win rate
        analytics_data.sort(key=lambda x: x['win_rate'], reverse=True)
        return render_template("analytics.html", stats=analytics_data)
    finally:
        db.close()

@app.route("/export")
@auth.login_required
def export_csv():
    import csv
    from io import StringIO
    from flask import Response
    
    db = get_session()
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
