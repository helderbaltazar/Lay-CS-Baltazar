import config
from data.league_config import get_league_avg
from models.poisson import PoissonDixonColes

from data.data_manager import DataManager

def calculate_lambdas(home_stats, away_stats, league_avg):
    avg_home, avg_away = league_avg
    
    h_scored = float(home_stats['goals']['for']['total']['home'] or 0) + 0.1
    h_conceded = float(home_stats['goals']['against']['total']['home'] or 0) + 0.1
    h_games = float(home_stats['fixtures']['played']['home'] or 0) + 0.1
    h_failed = float(home_stats.get('failed_to_score', {}).get('home') or 0)

    a_scored = float(away_stats['goals']['for']['total']['away'] or 0) + 0.1
    a_conceded = float(away_stats['goals']['against']['total']['away'] or 0) + 0.1
    a_games = float(away_stats['fixtures']['played']['away'] or 0) + 0.1
    a_failed = float(away_stats.get('failed_to_score', {}).get('away') or 0)

    # Cálculo Híbrido Avançado (xG Sintético) para Força de Ataque
    sxg_home = DataManager.calculate_synthetic_xg(h_scored, h_games, h_failed, avg_home)
    sxg_away = DataManager.calculate_synthetic_xg(a_scored, a_games, a_failed, avg_away)

    h_attack = sxg_home / avg_home
    h_defense = (h_conceded / h_games) / avg_away
    
    a_attack = sxg_away / avg_away
    a_defense = (a_conceded / a_games) / avg_home

    lam_home = h_attack * a_defense * avg_home
    lam_away = a_attack * h_defense * avg_away

    # Decaimento Exponencial / Peso de Fase Recente (Time-Decay)
    # Valorizamos o 'form' recente para inflar ou desinflar as lambdas
    def apply_recent_form(lam, form_str, is_home):
        if not form_str: return lam
        # Pegamos os últimos 5 jogos (já retornados pela API)
        recent = form_str[-5:]
        weight = 0.0
        # W = +5%, D = 0%, L = -5% por jogo recente (multiplicador de força)
        for char in recent:
            if char == 'W': weight += 0.05
            elif char == 'L': weight -= 0.05
        return lam * (1.0 + weight)
        
    h_form = home_stats.get('form', '')
    a_form = away_stats.get('form', '')
    
    lam_home = apply_recent_form(lam_home, h_form, True)
    lam_away = apply_recent_form(lam_away, a_form, False)

    lam_home = max(0.2, min(lam_home, 5.0))
    lam_away = max(0.2, min(lam_away, 5.0))

    return lam_home, lam_away

def scan_match(fixture, model, targets, source='API-Football'):
    fixture_info = fixture['fixture']
    league_info = fixture['league']
    home_team = fixture['teams']['home']
    away_team = fixture['teams']['away']

    # Removido filtro de odds e a chamada da API conforme solicitado pelo usuário
    # para economizar a cota de 100 requests/dia do plano Free.
    home_odd = None

    home_stats = DataManager.get_team_stats(home_team['id'], league_info['id'], source)
    away_stats = DataManager.get_team_stats(away_team['id'], league_info['id'], source)

    if not home_stats or not away_stats:
        return None

    league_avg = get_league_avg(league_info['id'])
    lam_home, lam_away = calculate_lambdas(home_stats, away_stats, league_avg)
    
    probs = model.get_probabilities(lam_home, lam_away, targets)
    extra_probs = model.get_extra_probabilities(lam_home, lam_away)

    real_score = None
    if fixture_info['status']['short'] in ['FT', 'AET', 'PEN']:
        goals = fixture.get('goals', {})
        if goals.get('home') is not None and goals.get('away') is not None:
            real_score = f"{goals['home']}-{goals['away']}"

    def evaluate_streaks(stats):
        form = stats.get('form', '')
        if not form: return None
        recent = form[-3:]
        if recent == 'WWW': return '🔥 HOT'
        if recent == 'LLL': return '❄️ COLD'
        return None

    home_streak = evaluate_streaks(home_stats)
    away_streak = evaluate_streaks(away_stats)

    return {
        'fixture_id': fixture_info['id'],
        'date': fixture_info['date'],
        'status': fixture_info['status']['short'],
        'real_score': real_score,
        'league': league_info['name'],
        'home': home_team['name'],
        'away': away_team['name'],
        'lambda_home': lam_home,
        'lambda_away': lam_away,
        'probabilities': probs,
        'extra_probabilities': extra_probs,
        'match_odd': home_odd,
        'home_streak': home_streak,
        'away_streak': away_streak
    }

def scan_all(fixtures, model, source='API-Football'):
    results = []
    for f in fixtures:
        res = scan_match(f, model, config.TARGET_SCORES, source)
        if res:
            results.append(res)
    return results

def rank_by_target(results, model):
    rankings = {target: [] for target in config.TARGET_SCORES}
    
    # Adicionamos as novas metodologias
    extra_markets = ["OVER_2.5", "UNDER_2.5", "UNDER_3.5", "UNDER_4.5", "BTTS_YES", "BACK_HOME", "LAY_DRAW", "UNDER_0.5_HT", "UNDER_1.5_HT"]
    for mkt in extra_markets:
        rankings[mkt] = []
    
    for target in config.TARGET_SCORES:
        sorted_res = sorted(results, key=lambda x: x['probabilities'][target])
        
        for idx, res in enumerate(sorted_res):
            rankings[target].append({
                'rank': idx + 1,
                'fixture_id': res['fixture_id'],
                'date': res['date'],
                'status': res['status'],
                'real_score': res.get('real_score'),
                'league': res['league'],
                'home': res['home'],
                'away': res['away'],
                'lambda_home': res['lambda_home'],
                'lambda_away': res['lambda_away'],
                'probability': res['probabilities'][target],
                'home_streak': res.get('home_streak'),
                'away_streak': res.get('away_streak')
            })
            
    for mkt in extra_markets:
        sorted_res = sorted(results, key=lambda x: x['extra_probabilities'][mkt], reverse=True)
        for idx, res in enumerate(sorted_res):
            rankings[mkt].append({
                'rank': idx + 1,
                'fixture_id': res['fixture_id'],
                'date': res['date'],
                'status': res['status'],
                'real_score': res.get('real_score'),
                'league': res['league'],
                'home': res['home'],
                'away': res['away'],
                'lambda_home': res['lambda_home'],
                'lambda_away': res['lambda_away'],
                'probability': res['extra_probabilities'][mkt],
                'home_streak': res.get('home_streak'),
                'away_streak': res.get('away_streak')
            })
            
    from analysis.ai_analyst import AIAnalyst
    # AI Analyst takes care of config.TARGET_SCORES mostly. We pass only those for adjustment if needed, but we can pass all.
    # To be safe with AI Analyst, we'll only pass the original TARGET_SCORES to it.
    sub_rankings = {t: rankings[t] for t in config.TARGET_SCORES}
    sub_rankings = AIAnalyst.analyze_top_rankings(sub_rankings)
    for t in config.TARGET_SCORES:
        rankings[t] = sub_rankings[t]
    
    # Re-calcula probabilidades com o fator de ajuste e re-ordena apenas para os placares alvo originais
    for target in config.TARGET_SCORES:
        for item in rankings[target]:
            adj = item.get('ai_adjustment_factor', 1.0)
            if adj != 1.0:
                new_lam_home = item['lambda_home'] * adj
                new_lam_away = item['lambda_away'] * adj
                new_probs = model.get_probabilities(new_lam_home, new_lam_away, [target])
                item['probability'] = new_probs[target]
                
        rankings[target].sort(key=lambda x: (
            -x.get('ai_confidence', 0),
            x.get('probability', 1.0)
        ))
        for idx, item in enumerate(rankings[target]):
            item['rank'] = idx + 1
            
    return rankings

def save_to_db(db, rankings):
    from database.models_db import Match, Prediction
    from dateutil.parser import parse
    
    match_cache = {}

    for target, records in rankings.items():
        for rec in records:
            fix_id = rec['fixture_id']
            if fix_id not in match_cache:
                match = db.query(Match).filter(Match.fixture_id == fix_id).first()
                if not match:
                    dt = parse(rec['date'])
                    import pytz, config
                    if dt.tzinfo:
                        dt = dt.astimezone(pytz.timezone(config.SCHEDULER_TIMEZONE))
                    dt = dt.replace(tzinfo=None)
                    match = Match(
                        fixture_id=fix_id,
                        date=dt,
                        league_name=rec['league'],
                        home_team=rec['home'],
                        away_team=rec['away'],
                        status=rec['status'],
                        real_score=rec.get('real_score')
                    )
                    db.add(match)
                    db.flush()
                else:
                    match.status = rec['status']
                    match.real_score = rec.get('real_score')
                match_cache[fix_id] = match

            match = match_cache[fix_id]
            
            pred = db.query(Prediction).filter(
                Prediction.match_id == match.id,
                Prediction.target_score == target
            ).first()
            
            if not pred:
                pred = Prediction(match_id=match.id, target_score=target)
                db.add(pred)
                
            pred.probability = rec['probability']
            pred.rank = rec['rank']
            pred.match_odd = rec.get('match_odd')
            pred.ai_verdict = rec.get('ai_verdict', 'APROVADO')
            pred.ai_confidence = rec.get('ai_confidence')
            pred.ai_critical_factor = rec.get('ai_critical_factor')
            pred.ai_analysis = rec.get('ai_analysis')
            
            if match.status in ['FT', 'AET', 'PEN'] and match.real_score:
                try:
                    h, a = map(int, match.real_score.split('-'))
                    total_goals = h + a
                    if target == "OVER_2.5":
                        pred.is_hit = total_goals > 2.5
                    elif target == "UNDER_2.5":
                        pred.is_hit = total_goals < 2.5
                    elif target == "UNDER_3.5":
                        pred.is_hit = total_goals < 3.5
                    elif target == "UNDER_4.5":
                        pred.is_hit = total_goals < 4.5
                    elif target == "UNDER_0.5_HT" or target == "UNDER_1.5_HT":
                        # We don't have HT score here easily, so we skip validation for now or mock it
                        # Since it's just for display of prediction, setting None
                        pred.is_hit = None
                    elif target == "BTTS_YES":
                        pred.is_hit = (h > 0 and a > 0)
                    elif target == "BACK_HOME":
                        pred.is_hit = (h > a)
                    elif target == "LAY_DRAW":
                        pred.is_hit = (h != a)
                    else:
                        # Original Lay CS
                        pred.is_hit = (match.real_score != target)
                except ValueError:
                        pred.is_hit = (match.real_score != target)
                        
                # Cálculo de lucro/perda (Simulação base 1 unidade stake)
                if pred.is_hit:
                    pred.profit_loss = 0.935
                else:
                    pred.profit_loss = -10.0 if "-" in target and target not in ["UNDER_2.5", "UNDER_3.5", "UNDER_4.5"] else -1.0
                    
    db.commit()
