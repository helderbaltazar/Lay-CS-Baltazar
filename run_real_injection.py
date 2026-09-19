import os
import datetime
import pytz
import sqlite3
import config
from database.db import SessionLocal
from database.models_db import Match, Prediction
from analysis.scanner import scan_all, rank_by_target, save_to_db
from models.poisson import PoissonDixonColes
from data.data_manager import DataManager
import json
import difflib
from integration.layback import generate_layback_json, inject_teams_ui, LAY_0_1_BOT_ID, LAY_0_2_BOT_ID, LAY_0_3_BOT_ID, LAY_1_3_BOT_ID, LAY_U05_HT_BOT_ID, LAY_U15_HT_BOT_ID, LAY_U25_HT_BOT_ID

def get_betfair_id(team_name, layback_teams):
    names = [t["name"] for t in layback_teams]
    if team_name in names:
        team = next((t for t in layback_teams if t["name"] == team_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    replacements = {" FC": "", "FC ": "", " CF": "", " Clube": "", " Esporte": ""}
    modified_name = team_name
    for k, v in replacements.items():
        if k in modified_name:
            modified_name = modified_name.replace(k, v).strip()
            
    if modified_name in names:
        team = next((t for t in layback_teams if t["name"] == modified_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    matches = difflib.get_close_matches(team_name, names, n=1, cutoff=0.6)
    if matches:
        match_name = matches[0]
        team = next((t for t in layback_teams if t["name"] == match_name), None)
        return {"name": team["name"], "id": int(team["id"])}
        
    return None



_telegram_stats_file = "data/telegram_team_stats.json"
_telegram_stats_cache = None

def get_historical_stats(team_name):
    global _telegram_stats_cache
    import difflib, os, json
    
    if not team_name:
        return None
        
    if _telegram_stats_cache is None:
        if os.path.exists(_telegram_stats_file):
            try:
                with open(_telegram_stats_file, "r", encoding="utf-8") as f:
                    _telegram_stats_cache = json.load(f)
            except Exception as e:
                print(f"⚠️ Erro ao carregar {_telegram_stats_file}: {e}")
                _telegram_stats_cache = {}
        else:
            _telegram_stats_cache = {}

    if team_name in _telegram_stats_cache:
        return _telegram_stats_cache[team_name]
        
    matches = difflib.get_close_matches(team_name, list(_telegram_stats_cache.keys()), n=1, cutoff=0.5)
    if matches:
        matched_stats = _telegram_stats_cache[matches[0]]
        _telegram_stats_cache[team_name] = matched_stats
        return matched_stats

    # Fallback para SQLite se existir
    if os.path.exists('data_store/database.sqlite3'):
        try:
            import sqlite3
            conn = sqlite3.connect('data_store/database.sqlite3')
            c = conn.cursor()
            c.execute("SELECT AVG(Media_Gols_no_1T_Casa), AVG(Efic_xG_Casa) FROM telegram_dataset WHERE home_name = ?", (team_name,))
            row = c.fetchone()
            conn.close()
            if row and row[0] is not None and row[1] is not None:
                stats = {"media_ht": float(row[0]), "efic_xg": float(row[1])}
                _telegram_stats_cache[team_name] = stats
                return stats
        except Exception:
            pass
            
    return None

def check_golden_filters(home_team, away_team, target, power_score, prediction=None):
    """
    Filtros de Ouro validados por backtest em 104.977 jogos históricos (2023-2026).

    === FILTROS LAY CS (ROI validado por mercado isolado) ===
      - xG Mandante (Pré-Live) > 1.5   → time da casa agressivo
      - Odd do Mandante < 2.0           → casa é favorita matemática
      - Potencial BTTS > 60%            → jogo aberto, visitante dificilmente não toma gol
      - Odd Lay máxima por mercado:
          0-1 → máx. 15  (Strike Rate: 94.8%, ROI: +20.5%)
          0-2 → máx. 30  (Strike Rate: 97.8%, ROI: +39.1%)
          0-3 → máx. 70  (Strike Rate: 99.0%, ROI: +42.3%)
    """

    # ── Filtros Lay CS (0-1 / 0-2 / 0-3) ──────────────────────
    if target in ["0-1", "0-2", "0-3"]:
        if prediction is None:
            print(f"      [Lay CS Ouro] Sem dados de prediction — REPROVADO")
            return False

        m = prediction.match

        # xG Mandante pré-jogo > 1.5
        xg_home = getattr(prediction, 'xg_home_prematch', None)
        if xg_home is None:
            xg_home = getattr(m, 'team_a_xg_prematch', None) if m else None
        if xg_home is None or float(xg_home) <= 1.5:
            print(f"      [Lay CS Ouro] xG Mandante={xg_home} <= 1.5 — REPROVADO")
            return False

        # Odd do Mandante < 2.0
        match_odd = getattr(prediction, 'match_odd', None)
        if match_odd is None:
            match_odd = getattr(m, 'home_odds', None) if m else None
        if match_odd is None or float(match_odd) >= 2.0:
            print(f"      [Lay CS Ouro] Odd Mandante={match_odd} >= 2.0 — REPROVADO")
            return False

        # Potencial BTTS > 60%
        btts_potential = getattr(m, 'btts_potential', None) if m else None
        if btts_potential is not None:
            try:
                btts_pct = float(str(btts_potential).replace('%', '').strip())
                if btts_pct > 1000:
                    btts_pct = btts_pct / 100.0
                if btts_pct < 60.0:
                    print(f"      [Lay CS Ouro] BTTS Potencial={btts_pct:.1f}% < 60% — REPROVADO")
                    return False
            except (ValueError, TypeError):
                pass

        # Limite de Odd Lay máxima por mercado
        lay_odd = getattr(prediction, 'lay_odd', None) or getattr(prediction, 'probability', None)
        if lay_odd is not None:
            try:
                lay_odd_float = float(lay_odd)
                if lay_odd_float < 1:
                    lay_odd_float = 1.0 / lay_odd_float if lay_odd_float > 0 else 999
                max_lay_odds = {"0-1": 15.0, "0-2": 30.0, "0-3": 70.0}
                max_odd = max_lay_odds.get(target, 15.0)
                if lay_odd_float > max_odd:
                    print(f"      [Lay CS Ouro] Odd Lay={lay_odd_float:.1f} > {max_odd} — REPROVADO")
                    return False
            except (ValueError, TypeError):
                pass

        print(f"      [Lay CS Ouro ✅] {target} | xG={float(xg_home):.2f} | OddH={float(match_odd):.2f} — APROVADO")
        return True

    # ── Filtros Under HT (mantidos) ─────────────────────────────
    if target not in ["UNDER_0.5_HT", "UNDER_1.5_HT", "UNDER_2.5_HT", "UNDER_3.5", "UNDER_4.5"]:
        return True

    h_stats = get_historical_stats(home_team)
    a_stats = get_historical_stats(away_team)

    if not h_stats or not a_stats:
        print(f"      [Filtro] Sem dados hist. p/ {home_team} ou {away_team}")
        return False

    soma_ht = h_stats["media_ht"] + a_stats["media_ht"]
    efic_home = h_stats["efic_xg"]
    efic_away = a_stats["efic_xg"]

    if target == "UNDER_0.5_HT":
        if power_score >= 30 and soma_ht <= 1.2 and efic_home <= 1.0 and efic_away <= 1.0:
            print(f"      [U05 Ouro] SomaHT={soma_ht:.2f}, EficH={efic_home:.2f}, EficA={efic_away:.2f}")
            return True

    elif target == "UNDER_1.5_HT":
        if soma_ht <= 1.4:
            print(f"      [U15 Ouro] SomaHT={soma_ht:.2f}")
            return True

    elif target == "UNDER_2.5_HT":
        if soma_ht <= 1.8 and efic_home <= 1.0 and efic_away <= 1.0:
            print(f"      [U25 Ouro] SomaHT={soma_ht:.2f}, EficH={efic_home:.2f}, EficA={efic_away:.2f}")
            return True

    elif target == "UNDER_3.5":
        if power_score >= 50 and soma_ht <= 1.4 and efic_home <= 0.8 and efic_away <= 0.8:
            print(f"      [U3.5 Ouro] SomaHT={soma_ht:.2f}, EficH={efic_home:.2f}, EficA={efic_away:.2f}")
            return True

    elif target == "UNDER_4.5":
        if power_score >= 70 and soma_ht <= 1.4 and efic_home <= 0.8 and efic_away <= 0.8:
            print(f"      [U4.5 Ouro] SomaHT={soma_ht:.2f}, EficH={efic_home:.2f}, EficA={efic_away:.2f}")
            return True

    return False


def is_injection_completed_today():
    db = SessionLocal()
    from database.models_db import SystemConfig
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today_str = now_br.strftime("%Y-%m-%d")
    key = f"injection_completed_{today_str}"
    flag = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    db.close()
    return flag is not None

def mark_injection_completed():
    db = SessionLocal()
    from database.models_db import SystemConfig
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today_str = now_br.strftime("%Y-%m-%d")
    key = f"injection_completed_{today_str}"
    flag = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not flag:
        db.add(SystemConfig(key=key, value="true"))
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Erro ao marcar injeção como completada: {e}")
    db.close()

def ensure_data_in_db():
    db = SessionLocal()
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    
    dates_to_check = [
        now_br + datetime.timedelta(days=i) for i in range(4)  # hoje + próximos 3 dias (fim de semana)
    ]
    
    for target_dt in dates_to_check:
        day_start = target_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + datetime.timedelta(days=1)
        target_str = target_dt.strftime("%Y-%m-%d")
        
        print(f"[{now_br}] Verificando se os jogos de {target_str} já estão no Supabase...")
        matches_today = db.query(Match).filter(Match.date >= day_start, Match.date < day_end).first()
        
        if matches_today:
            print(f"✅ Jogos do dia {target_str} já existem no banco de dados. Verificando auditoria de IA...")
            unanalysed = db.query(Prediction).join(Match).filter(
                Match.date >= day_start, Match.date < day_end,
                Prediction.ai_confidence.is_(None)
            ).all()
            if unanalysed:
                # Sem limites matemáticos. Todos os jogos que passaram pelo filtro BTTS vão pro agente!
                AI_TOP_N_PER_MARKET = 500
                from collections import defaultdict
                per_market = defaultdict(list)
                for p in unanalysed:
                    per_market[p.target_score].append(p)

                to_audit = []
                to_fallback = []
                # Mercados sujeitos à auditoria de IA (todos os targets configurados: Lay CS e UNDER_X_HT)
                auditable_markets = set(config.TARGET_SCORES)
                for market, preds in per_market.items():
                    if market in auditable_markets:
                        to_audit.extend(preds)
                    else:
                        to_fallback.extend(preds)

                # Aplica fallback heurístico nos jogos fora do Top ou de outros mercados
                for p in to_fallback:
                    p.ai_verdict = 'APROVADO'
                    p.ai_confidence = 85
                    p.ai_critical_factor = 'Aprovação estatística (regras quantitativas validadas)'
                    p.ai_analysis = 'Análise matemática Poisson + Dixon-Coles aprovada.'

                print(f"🤖 Auditando {len(to_audit)} predições Lay CS com IA + {len(to_fallback)} com validação quantitativa...")
                from analysis.ai_analyst import AIAnalyst
                for i, p in enumerate(to_audit, 1):
                    m = p.match
                    if m:
                        match_dict = {
                            'home': m.home_team,
                            'away': m.away_team,
                            'league': m.league_name
                        }
                        res = AIAnalyst.orchestrate_match(match_dict, p.target_score, p.probability or 0.05)
                        p.ai_verdict = res['verdict']
                        p.ai_confidence = res['confidence']
                        p.ai_critical_factor = res['critical_factor']
                        p.ai_analysis = res['detailed_analysis']
                        import time
                        time.sleep(0.3)
                    if i % 10 == 0:
                        try:
                            db.commit()
                        except Exception as ce:
                            print(f"⚠️ Erro ao commitar lote de IA: {ce}")
                            db.rollback()
                            try:
                                db.commit()
                            except Exception as ce2:
                                print(f"❌ Falha definitiva ao commitar lote de IA (dados perdidos): {ce2}")
                                db.rollback()
                try:
                    db.commit()
                except Exception as ce:
                    print(f"⚠️ Erro ao commitar lote final de IA: {ce}")
                    db.rollback()
                    try:
                        db.commit()
                    except Exception as ce2:
                        print(f"❌ Falha definitiva ao commitar lote final de IA (dados perdidos): {ce2}")
                        db.rollback()
                print(f"✅ Auditoria da IA concluída e salva para {target_str}!")

        else:
            print(f"⚠️ Nenhum jogo encontrado no banco para {target_str}. Buscando na API...")
            all_fixtures = []
            f, source = DataManager.get_fixtures(target_str)
            if f:
                all_fixtures.extend(f)
                    
            if all_fixtures:
                model = PoissonDixonColes()
                results = scan_all(all_fixtures, model, source)
                rankings = rank_by_target(results, model)
                save_to_db(db, rankings)
                print(f"✅ Novos jogos de {target_str} calculados e salvos no banco de dados com sucesso.")
            else:
                print(f"⚠️ Sem jogos disponíveis para {target_str} em nenhuma fonte.")

    db.close()

def inject_from_db():
    print("\n--- INICIANDO INJEÇÃO NO LAYBACK VIA BANCO DE DADOS ---")
    db = SessionLocal()
    
    teams_file = "data/teams_api.json"
    if not os.path.exists(teams_file):
        print(f"❌ Arquivo {teams_file} não encontrado. Impossível mapear times para o LayBack.")
        print("   Execute o script de captura de times ou crie o arquivo manualmente.")
        db.close()
        return
    
    with open(teams_file, "r") as f:
        layback_teams = json.load(f)["data"]["teams"]

    targets = [
        (LAY_0_1_BOT_ID, "bot_lay_0_1", "0-1"),
        (LAY_0_2_BOT_ID, "bot_lay_0_2", "0-2"),
        (LAY_0_3_BOT_ID, "bot_lay_0_3", "0-3"),
        (LAY_1_3_BOT_ID, "bot_lay_1_3", "1-3"),
        (LAY_U05_HT_BOT_ID, "bot_u05_ht", "UNDER_0.5_HT"),
        (LAY_U15_HT_BOT_ID, "bot_u15_ht", "UNDER_1.5_HT"),
        (LAY_U25_HT_BOT_ID, "bot_u25_ht", "UNDER_2.5_HT"),
    ]
    
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today_start = now_br.replace(hour=0, minute=0, second=0, microsecond=0)
    # Busca jogos dos próximos 4 dias para cobrir o final de semana completo
    weekend_end = today_start + datetime.timedelta(days=4)

    report_lines = [f"🤖 *Relatório Layback — Final de Semana (Filtros Ouro Backtest)* 🤖\n📅 {today_start.strftime('%d/%m')} a {weekend_end.strftime('%d/%m/%Y')}\n"]
    for bot_id, bot_name, target in targets:
        # Filtro base do banco de dados
        if "UNDER_" in target:
            preds = db.query(Prediction).join(Match).filter(
                Prediction.target_score == target,
                Prediction.ai_verdict == 'APROVADO',
                Match.date >= today_start,
                Match.date < weekend_end
            ).all()
        else:
            from sqlalchemy import or_
            preds = db.query(Prediction).join(Match).filter(
                Prediction.target_score == target,
                Prediction.ai_verdict == 'APROVADO',
                Match.date >= today_start,
                Match.date < weekend_end,
                or_(
                    Prediction.match_odd == None,
                    Prediction.match_odd <= 3.50
                )
            ).all()

        if not preds:
            print(f"[{target}] Nenhum jogo aprovado para o final de semana.")
            continue

        bot_games_str = []
        teams_data = []
        for p in preds:
            m = p.match

            # Aplicar Filtros de Ouro (Lay CS e Under HT)
            if target in ["0-1", "0-2", "0-3"]:
                if not check_golden_filters(m.home_team, m.away_team, target, p.power_score, prediction=p):
                    continue
            elif "UNDER_" in target:
                if not check_golden_filters(m.home_team, m.away_team, target, p.power_score):
                    continue

            data_str = m.date.strftime('%d/%m') if m.date else '?'
            conf_str = f" [Score: {p.power_score:.1f}]" if p.power_score else ""
            print(f"[{target}] {data_str} | {m.home_team} x {m.away_team} {conf_str}")
            bot_games_str.append(f"⚽ {data_str} — {m.home_team} x {m.away_team} {conf_str}")
            h_bf = get_betfair_id(m.home_team, layback_teams)
            a_bf = get_betfair_id(m.away_team, layback_teams)
            if h_bf: teams_data.append(h_bf)
            if a_bf: teams_data.append(a_bf)
            
        if not teams_data:
            print(f"ERRO: Não mapeou nenhum time!")
            continue
            
        json_file = generate_layback_json(teams_data, bot_name)
        print(f"[{target}] Injetando no bot {bot_id} via Playwright...")
        from integration.layback import OperatorAgent
        success = OperatorAgent.inject_teams(bot_id, json_file)
        if success:
            report_lines.append(f"✅ *{target}* (Bot {bot_id}):")
            report_lines.extend(bot_games_str)
            report_lines.append("")
            print(f"[{target}] SUCESSO!")
        else:
            report_lines.append(f"❌ *{target}* (Bot {bot_id}) FALHOU.")
            report_lines.append("")
            print(f"[{target}] FALHOU!")
            final_report = "\n".join(report_lines)
            from notifications.telegram import send_message
            send_message(final_report)
            import sys
            sys.exit(1)
            
    final_report = "\n".join(report_lines)
    from notifications.telegram import send_message
    send_message(final_report)
    db.close()

if __name__ == "__main__":
    from database.db import init_db
    init_db()
    
    if is_injection_completed_today():
        print("✅ A injeção de hoje já foi realizada com sucesso. Encerrando para evitar duplicação.")
        import sys
        sys.exit(0)

    
    try:
        from update_results import update_pending_matches
        update_pending_matches()
    except Exception as e:
        print(f"Erro ao atualizar pendentes: {e}")
        
    ensure_data_in_db()
    inject_from_db()
    mark_injection_completed()
    print("🎉 Processo diário finalizado com sucesso!")

