# PROJECT_CONTEXT.md — Automação Lay CS

> Arquivo de memória de longo prazo. Leitura obrigatória no início de toda sessão.
> Última atualização: 2026-09-10

## Visão Geral

Sistema de automação para apostas Lay Correct Score. Scanner diário que rankeia jogos por menor probabilidade de placares-alvo usando modelo Poisson + Dixon-Coles. Resultados são exibidos em dashboard web e injetados automaticamente no LayBack.

## Estado Atual

| Componente | Status |
|---|---|
| Scanner Poisson + Dixon-Coles | ✅ Funcional |
| Dashboard Web (Flask/Render) | ✅ Funcional |
| Injeção automática LayBack (Playwright) | ✅ Funcional |
| Pipeline CI/CD (GitHub Actions) | ✅ Funcional |
| IA Especialista (Gemini 2.0 Flash) | ✅ Funcional |
| Odds Cascade (The Odds API) | ✅ Parcial (apenas nível 1 implementado) |
| BTTS obrigatório | ⚠️ Enforcement pendente |
| Arquitetura Agêntica | 🟡 Fase 0 (Pré-Agêntica) |

## Decisões Críticas

1. **Modelo Estatístico:** Poisson + Dixon-Coles (ρ = -0.10, MAX_GOALS = 7)
2. **Placares-alvo:** 0-1, 0-2, 0-3, 1-3, UNDER_0.5_HT, UNDER_1.5_HT, UNDER_2.5_HT
3. **API Principal:** API-Football (Free plan: 100 req/dia)
4. **Banco de Dados:** Supabase (PostgreSQL) em produção, SQLite local para testes
5. **Frontend:** Flask + Gunicorn no Render
6. **IA:** Gemini 2.0 Flash (análise de jogos), Gemini 1.5 Pro (SRE futuro)
7. **Ligas:** 23 ligas/copas principais configuradas em `data/league_config.py`

## Regras de Negócio Inviolavéis

- **Guardrails financeiros:** MAX_LIABILITY hardcoded em config.py, NUNCA sobrescrito por agente
- **BTTS obrigatório:** Jogo sem odd de BTTS SIM não pode ser analisado pela IA
- **Proteção de banco:** Agentes só têm SELECT/INSERT/UPDATE, NUNCA DELETE/DROP
- **Rate limiting:** 100 req/dia API-Football, sleep(6.1) entre requests, cache obrigatório
- **TDD:** Nenhum commit sem todos os testes passando

## Estrutura de Diretórios Chave

```
analysis/     → Scanner, odds_fetcher, ai_analyst, blacklist
data/         → api_football, odds_api, cache, league_config
database/     → db.py (SQLAlchemy), models_db.py
integration/  → layback.py (Playwright injection)
models/       → poisson.py (Dixon-Coles)
web/          → app.py (Flask dashboard)
tests/        → unit/, integration/, web/
scripts/      → Utilitários (verify_cookies, update_opta, etc.)
```

## Variáveis de Ambiente Obrigatórias

| Var | Uso |
|---|---|
| API_FOOTBALL_KEY | API-Football (scanner) |
| ODDS_API_KEY | The Odds API (odds) |
| GEMINI_API_KEY | Gemini (IA especialista) |
| DATABASE_URL | Supabase PostgreSQL |
| LAYBACK_EMAIL/PASSWORD | Login automático LayBack |
| DASHBOARD_USERNAME/PASSWORD | Autenticação do dashboard web |
| TELEGRAM_BOT_TOKEN/CHAT_ID | Alertas Telegram |
| RENDER_API_KEY/SERVICE_ID | Deploy automático Render |
