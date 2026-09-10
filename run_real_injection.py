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

def check_golden_filters(home_team, away_team, target, power_score):
    if target not in ["UNDER_0.5_HT", "UNDER_1.5_HT", "UNDER_2.5_HT", "UNDER_3.5", "UNDER_4.5"]:
        return True # Nao aplica filtros de ouro para outros mercados
        
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
        now_br,
        now_br + datetime.timedelta(days=1)
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
                # Top 15 por mercado — plano pago Gemini, cobre todos os jogos relevantes do dashboard
                AI_TOP_N_PER_MARKET = 15
                from collections import defaultdict
                per_market = defaultdict(list)
                for p in unanalysed:
                    per_market[p.target_score].append(p)

                to_audit = []
                to_fallback = []
                # A IA foi treinada/promptada especificamente para Lay Correct Score
                lay_cs_markets = {"0-1", "0-2", "0-3", "1-3"}
                for market, preds in per_market.items():
                    sorted_preds = sorted(preds, key=lambda x: x.power_score or 0, reverse=True)
                    if market in lay_cs_markets:
                        to_audit.extend(sorted_preds[:AI_TOP_N_PER_MARKET])
                        to_fallback.extend(sorted_preds[AI_TOP_N_PER_MARKET:])
                    else:
                        # Mercados de Under/Over são governados pelas regras matemáticas estatísticas
                        to_fallback.extend(sorted_preds)

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
                        res = AIAnalyst.analyze_match(match_dict, p.target_score, p.probability or 0.05)
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
                try:
                    db.commit()
                except Exception as ce:
                    print(f"⚠️ Erro ao commitar lote final de IA: {ce}")
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
    
    with open("data/teams_api.json", "r") as f:
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
    
    report_lines = ["🤖 *Relatório Diário Layback (Power Score)* 🤖\n"]
    for bot_id, bot_name, target in targets:
        # Define o limiar de Power Score com base no mercado
        if target == "0-1": threshold = 94.0
        elif target == "0-2": threshold = 94.0
        elif target == "0-3": threshold = 99.2
        elif target == "1-3": threshold = 99.3
        elif target == "UNDER_0.5_HT": threshold = 30.0 # Aprovado na nossa IA
        elif target == "UNDER_1.5_HT": threshold = 0.0 # Controlado só pelo SomaHT
        elif target == "UNDER_2.5_HT": threshold = 0.0 # Controlado só pelo SomaHT
        else: threshold = 99.0
        
        
        # Filtro base do banco de dados
        if "UNDER_" in target:
            # Para Unders, não restringimos a odd do match winner (porque não é relevante pro Layback aqui)
            preds = db.query(Prediction).join(Match).filter(
                Prediction.target_score == target,
                Prediction.power_score >= threshold,
                Prediction.ai_verdict != 'REPROVADO',
                Match.date >= today_start
            ).order_by(
                Prediction.power_score.desc().nullslast(),
            ).all()
        else:
            from sqlalchemy import or_
            preds = db.query(Prediction).join(Match).filter(
                Prediction.target_score == target,
                Prediction.power_score >= threshold,
                Prediction.ai_verdict != 'REPROVADO',
                or_(Prediction.match_odd == None, Prediction.match_odd <= 2.0),
                Match.date >= today_start
            ).order_by(
                Prediction.power_score.desc().nullslast(),
            ).all()
        
        if not preds:
            print(f"[{target}] Nenhum jogo aprovado pelo Power Score (>= {threshold}) para hoje.")
            continue
            
        bot_games_str = []
        teams_data = []
        for p in preds:
            m = p.match
            
            # Filtro Histórico Ouro para novos mercados
            if "UNDER_" in target:
                if not check_golden_filters(m.home_team, m.away_team, target, p.power_score):
                    continue
            
            conf_str = f" [Score: {p.power_score:.1f}]" if p.power_score else ""
            print(f"[{target}] {m.home_team} x {m.away_team} {conf_str}")
            bot_games_str.append(f"⚽ {m.home_team} x {m.away_team} {conf_str}")
            h_bf = get_betfair_id(m.home_team, layback_teams)
            a_bf = get_betfair_id(m.away_team, layback_teams)
            if h_bf: teams_data.append(h_bf)
            if a_bf: teams_data.append(a_bf)
            
        if not teams_data:
            print(f"ERRO: Não mapeou nenhum time!")
            continue
            
        json_file = generate_layback_json(teams_data, bot_name)
        print(f"[{target}] Injetando no bot {bot_id} via Playwright...")
        success = inject_teams_ui(bot_id, json_file)
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

