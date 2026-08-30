import datetime
import pytz
import config
from database.db import SessionLocal
from database.models_db import Match, Prediction
from analysis.scanner import scan_all, rank_by_target, save_to_db
from models.poisson import PoissonDixonColes
from data.data_manager import DataManager
import json
import difflib
from integration.layback import generate_layback_json, inject_teams_ui, LAY_0_1_BOT_ID, LAY_0_2_BOT_ID, LAY_0_3_BOT_ID, LAY_1_3_BOT_ID

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

def ensure_data_in_db():
    db = SessionLocal()
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today_start = now_br.replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"[{now_br}] Verificando se os jogos de hoje já estão no Supabase...")
    matches_today = db.query(Match).filter(Match.date >= today_start).first()
    
    if matches_today:
        print("✅ Jogos do dia já existem no banco de dados. Verificando auditoria de IA...")
        unanalysed = db.query(Prediction).join(Match).filter(Match.date >= today_start, Prediction.ai_confidence.is_(None)).all()
        if unanalysed:
            print(f"🤖 Auditando {len(unanalysed)} predições com IA...")
            from analysis.ai_analyst import AIAnalyst
            for i, p in enumerate(unanalysed, 1):
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
                if i % 20 == 0:
                    try:
                        db.commit()
                    except Exception as ce:
                        print(f"⚠️ Erro ao commitar lote de IA: {ce}")
            try:
                db.commit()
            except Exception as ce:
                print(f"⚠️ Erro ao commitar lote final de IA: {ce}")
            print("✅ Auditoria da IA concluída e salva no Supabase!")
    else:
        print("⚠️ Nenhum jogo encontrado no banco para hoje. Buscando na API...")
        today_str = now_br.strftime("%Y-%m-%d")
        all_fixtures = []
        f, source = DataManager.get_fixtures(today_str)
        if f:
            all_fixtures.extend(f)
                
        if all_fixtures:
            model = PoissonDixonColes()
            results = scan_all(all_fixtures, model, source)
            rankings = rank_by_target(results)
            save_to_db(db, rankings)
            print("✅ Novos jogos calculados e salvos no banco de dados com sucesso.")
        else:
            print("❌ Nenhum jogo configurado nas ligas para hoje retornado pela API.")
    
    db.close()

def inject_from_db():
    print("\\n--- INICIANDO INJEÇÃO NO LAYBACK VIA BANCO DE DADOS ---")
    db = SessionLocal()
    
    with open("data/teams_api.json", "r") as f:
        layback_teams = json.load(f)["data"]["teams"]

    targets = [
        (LAY_0_1_BOT_ID, "bot_lay_0_1", "0-1"),
        (LAY_0_2_BOT_ID, "bot_lay_0_2", "0-2"),
        (LAY_0_3_BOT_ID, "bot_lay_0_3", "0-3"),
        (LAY_1_3_BOT_ID, "bot_lay_1_3", "1-3"),
    ]
    
    now_br = datetime.datetime.now(pytz.timezone(config.SCHEDULER_TIMEZONE))
    today_start = now_br.replace(hour=0, minute=0, second=0, microsecond=0)
    
    report_lines = ["🤖 *Relatório Diário Layback (Top 5 Confiança IA)* 🤖\n"]
    for bot_id, bot_name, target in targets:
        preds = db.query(Prediction).join(Match).filter(
            Prediction.target_score == target,
            Prediction.ai_verdict != 'VETADO',
            Match.date >= today_start
        ).order_by(
            Prediction.ai_confidence.desc().nullslast(),
            Prediction.probability.asc()
        ).limit(5).all()
        
        if not preds:
            print(f"[{target}] Nenhum jogo aprovado pela IA no banco para hoje.")
            continue
            
        bot_games_str = []
        teams_data = []
        for p in preds:
            m = p.match
            conf_str = f" [IA: {p.ai_confidence}%]" if p.ai_confidence else ""
            print(f"[{target}] Rank {p.rank}: {m.home_team} x {m.away_team} (Prob: {p.probability:.2%}){conf_str}")
            bot_games_str.append(f"⚽ {m.home_team} x {m.away_team} ({p.probability:.2%}){conf_str}")
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
    
    try:
        from update_results import update_pending_matches
        update_pending_matches()
    except Exception as e:
        print(f"Erro ao atualizar pendentes: {e}")
        
    ensure_data_in_db()
    inject_from_db()
