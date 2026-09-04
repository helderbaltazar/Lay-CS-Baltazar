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
    
    rankings = {t: {'approved': [], 'rejected': []} for t in config.TARGET_SCORES}
    
    # Lista temporária para ordenar tudo primeiro
    temp_rankings = {t: [] for t in config.TARGET_SCORES}
    
    for m in matches:
        for p in m.predictions:
            if p.target_score in temp_rankings:
                temp_rankings[p.target_score].append({
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
                    'ai_analysis': p.ai_analysis or '',
                    'fair_odd': round(100.0 / (p.probability * 100), 2) if p.probability > 0 else 0,
                    'edge': round(((p.match_odd / (1.0 / p.probability)) - 1) * 100, 1) if p.match_odd and p.probability > 0 else 0,
                    'fixture_id': m.fixture_id
                })
                
    for t in config.TARGET_SCORES:
        # Ordena: Aprovados primeiro, Confiança desc, Prob asc
        temp_rankings[t].sort(key=lambda x: (
            0 if x['ai_verdict'] != 'VETADO' else 1, 
            -x.get('ai_confidence', 0), 
            x.get('probability', 1.0)
        ))
        
        for idx, item in enumerate(temp_rankings[t]):
            item['rank'] = idx + 1
            if item['rank'] <= 5 and item['ai_verdict'] != 'VETADO':
                rankings[t]['approved'].append(item)
            else:
                rankings[t]['rejected'].append(item)
        
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
            Prediction.rank <= 5
        ).first()
        
        top5_winrate = (top5_stats.hits / top5_stats.total * 100) if top5_stats and top5_stats.total > 0 else 0

        # AI Verdict Stats
        ai_stats_raw = db.query(
            Prediction.ai_verdict,
            func.count(Match.id).label('total_games'),
            func.sum(case((Prediction.is_hit == True, 1), else_=0)).label('hits'),
            func.sum(case((Prediction.is_hit == False, 1), else_=0)).label('misses')
        ).join(Match).filter(
            Match.status.in_(['FT', 'AET', 'PEN']),
            Prediction.is_hit != None,
            Prediction.ai_verdict != None
        ).group_by(Prediction.ai_verdict).all()
        
        ai_data = []
        for a in ai_stats_raw:
            tot = a.hits + a.misses
            wr = (a.hits / tot * 100) if tot > 0 else 0
            ai_data.append({
                'verdict': a.ai_verdict,
                'total_games': tot,
                'hits': a.hits,
                'misses': a.misses,
                'win_rate': round(wr, 2)
            })

        # Calcula Win-Rate Confiança >= 95
        high_conf_stats = db.query(
            func.count(Match.id).label('total'),
            func.sum(case((Prediction.is_hit == True, 1), else_=0)).label('hits')
        ).join(Prediction).filter(
            Match.status.in_(['FT', 'AET', 'PEN']),
            Prediction.is_hit != None,
            Prediction.ai_confidence >= 95
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
            Prediction.rank <= 5
        ).group_by(Match.date).order_by(Match.date).all()
        
        chart_labels = []
        chart_data = []
        acc_profit = 0.0
        for row in curve_query:
            chart_labels.append(str(row.date))
            acc_profit += float(row.daily_profit or 0.0)
            chart_data.append(round(acc_profit, 2))
            
        return render_template('analytics.html', analytics_data=analytics_data, top5_winrate=round(top5_winrate, 2), high_winrate=round(high_winrate, 2), chart_labels=chart_labels, chart_data=chart_data)
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

@app.route('/api/analysis')
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
    return jsonify(data)

@app.route("/methodologies")
@auth.login_required
def methodologies():
    db = get_session()
    try:
        from sqlalchemy import func
        # 1. Obter a curva de lucro diário para calcular o Max Drawdown
        curve_query = db.query(
            Match.date,
            func.sum(Prediction.profit_loss).label('daily_profit')
        ).join(Prediction).filter(
            Match.status.in_(['FT', 'AET', 'PEN']),
            Prediction.is_hit != None,
            Prediction.rank <= 5
        ).group_by(Match.date).order_by(Match.date).all()
        
        acc_profit = 0.0
        peak = 0.0
        max_drawdown = 0.0
        
        profits = []
        for row in curve_query:
            daily = float(row.daily_profit or 0.0)
            acc_profit += daily
            profits.append(daily)
            
            if acc_profit > peak:
                peak = acc_profit
            
            drawdown = peak - acc_profit
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                
        # 2. Simulação de Monte Carlo (Caminhos Aleatórios)
        import random
        mc_simulations = 100
        mc_results = []
        
        if profits:
            for _ in range(mc_simulations):
                # Embaralha os retornos diários para simular uma nova sequência
                shuffled = profits.copy()
                random.shuffle(shuffled)
                
                sim_acc = 0.0
                sim_curve = []
                for p in shuffled:
                    sim_acc += p
                    sim_curve.append(sim_acc)
                mc_results.append(sim_curve)
                
        # Calcula o risco de ruína ou Pior Cenário de Monte Carlo (5º percentil)
        worst_cases = []
        if mc_results:
            final_balances = [path[-1] for path in mc_results]
            final_balances.sort()
            mc_worst_case = final_balances[int(mc_simulations * 0.05)] # 5% pior cenário
        else:
            mc_worst_case = 0.0
            
        # 3. Recomendações do Dia
        import datetime
        import pytz
        now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
        today_str = now_br.strftime("%Y-%m-%d")
        
        matches_today = db.query(Match).filter(func.date(Match.date) == today_str).all()
        
        recs = {
            "OVER_2.5": [], "BACK_HOME": [], "BTTS_YES": [],
            "UNDER_2.5": [], "UNDER_3.5": [], "UNDER_4.5": [],
            "UNDER_0.5_HT": [], "UNDER_1.5_HT": []
        }
        
        for m in matches_today:
            for p in m.predictions:
                if p.target_score in recs:
                    recs[p.target_score].append({
                        'home': m.home_team,
                        'away': m.away_team,
                        'prob': p.probability,
                        'league': m.league_name
                    })
                    
        for k in recs:
            recs[k].sort(key=lambda x: x['prob'], reverse=True)
            recs[k] = recs[k][:5] # Top 5
            
    finally:
        db.close()
        
    return render_template('methodologies.html', 
                           max_drawdown=round(max_drawdown, 2),
                           mc_worst_case=round(mc_worst_case, 2),
                           recs=recs)
