# Plano de Migração Agêntica — Lay CS

> Roadmap para evolução do sistema de automação de regras fixas para arquitetura multi-agente.
> Última atualização: 2026-09-10

## Princípios

1. **Implementação sequencial** — Nunca pular fases
2. **Degradação graciosa** — Falha em qualquer fase ativa o comportamento da fase anterior
3. **Feature flags** — Cada fase desativável via variável de ambiente
4. **Guardrails financeiros** — Limites de stake hardcoded, nunca sobrescritos por agente
5. **Proteção de banco** — Agentes só têm SELECT/INSERT/UPDATE

## Fases

### Fase 0: Saneamento de Dados (Pré-Agêntica)
**Status:** 🟡 Em andamento

**Objetivo:** Garantir que todos os dados necessários para os agentes estejam disponíveis e validados.

**Tarefas:**
- [x] Scanner Poisson + Dixon-Coles funcional
- [x] Odds cascade nível 1 (The Odds API)
- [ ] Captura garantida de match_odd e btts_odd
- [ ] Contrato de dados `MatchContext` tipado
- [ ] H2H e Must-Win implementados
- [ ] Smoke test no CI antes da injeção

### Fase 1: O Conselheiro Silencioso
**Status:** 🔴 Não iniciada

**Objetivo:** Um agente único (Olheiro) analisa jogos rejeitados pelo scanner e pode resgatá-los com justificativa.

**Modelo:** Gemini 2.0 Flash
**Feature flag:** `AGENT_PHASE1_ENABLED=true/false`

### Fase 2: O Comitê de Decisão
**Status:** 🔴 Não iniciada

**Objetivo:** Múltiplos agentes (Olheiro + Estratégico + Financeiro) votam em cada jogo.

### Fase 3: Tool-Calling Dinâmico
**Status:** 🔴 Não iniciada

**Objetivo:** Agentes podem chamar ferramentas (APIs, banco de dados) dinamicamente.

**Modelo:** Gemini 2.5 Pro (suporte nativo a function calling)

### Fase 4: Injeção Resiliente (ReAct)
**Status:** 🔴 Não iniciada

**Objetivo:** Agente operador com loop ReAct para injeção no LayBack.

### Fase 5: Auto-Healing SRE
**Status:** 🔴 Não iniciada

**Objetivo:** Agente SRE monitora logs do GitHub Actions e corrige falhas automaticamente.

**Modelo:** Gemini 1.5 Pro (janela de 1M tokens)

## Cascata de Captura de Odds

1. **The Odds API** → `GET /v4/odds/?markets=h2h,btts`
2. **API-Football** → `GET /v3/odds?fixture={id}`
3. **Sofascore API** → `GET api.sofascore.com/api/v1/event/{id}/odds/1/all`
4. **OddsPortal (Playwright)** → Navegar até a partida e extrair DOM
5. Falha total → `odds_source: "unavailable"` → jogo excluído

## Recomendação de Modelos

| Camada | Modelo | Motivo |
|---|---|---|
| Análise de jogos (Fase 1-2) | Gemini 2.0 Flash | Rápido, barato, boa saída JSON |
| Tool-Calling (Fase 3) | Gemini 2.5 Pro | Suporte nativo a funções |
| Auto-Healing (Fase 5) | Gemini 1.5 Pro | Janela de 1M tokens |
| Fallback geral | Claude 3.5 Haiku/Sonnet | Alternativa se Gemini indisponível |
