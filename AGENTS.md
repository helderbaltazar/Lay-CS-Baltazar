# Regras do Projeto (Automação Lay CS)

Você é o desenvolvedor principal da automação "Lay CS" e atua como um engenheiro autônomo (Looping Engineer). Siga estas diretrizes irrestritamente em todas as interações.

## 1. Looping Engineering e TDD Autônomo
* Todo desenvolvimento deve seguir um ciclo de feedback fechado: **Escrever Teste → Escrever Código → Rodar Teste no Sandbox → Consertar Erros → Commit**.
* Só conclua a tarefa quando o teste automatizado correspondente estiver passando (`python -m pytest`).
* **Regra de TDD para Agentes:** Toda nova funcionalidade da arquitetura agêntica deve ter um teste escrito ANTES da implementação.

## 2. Testes e Proteção Contra Regressão

* **REGRA DE OURO:** Jamais altere ou versione código sem garantir que a suíte completa de testes (`pytest tests/ -v`) continue 100% verde.

### Estrutura de Testes por Camada
* `tests/unit/` → Funções isoladas com dados FIXOS e MOCKS. **Nunca** chama internet ou banco real.
* `tests/integration/` → Fluxos completos com banco SQLite em memória (conftest.py já configura).
* `tests/web/` → UI do dashboard (HTTP 200, componentes visuais).

### Baseline de Regressão Inviolável
* Antes de qualquer nova implementação, rodar: `pytest tests/ -v -k "cruzeiro or atletico" --tb=short`

### Smoke Test Obrigatório no CI
* `pytest tests/unit/ -v --tb=short -x` deve rodar ANTES do job de injeção.
* Se falhar, a injeção NÃO deve ser iniciada.

## 3. Versionamento Seguro e Rollback
* Faça commits granulares ao fim de cada funcionalidade.
* Nunca faça commits de códigos quebrados.
* Utilize `git tag vX.Y.Z` a cada grande marco. Para fases agênticas: `git tag agentic-fase-N`.
* O `.gitignore` deve isolar estritamente as pastas `logs/`, `cache/` e o BD.

## 4. Preservação de Contexto (Memory Management)
* **Ponto de Partida:** Toda vez que inicializar neste projeto, DEVE LER: `PROJECT_CONTEXT.md`, `docs/plano_implementacao.md` e `docs/plano_migracao_agentica.md`.
* Se a sessão estiver longa, delegue tarefas secundárias a subagentes (`invoke_subagent`).

## 5. Escopo e Restrições Técnicas
* Modelo Estatístico: Poisson + correção Dixon-Coles (ρ = -0.10).
* Limite Crítico de API: Free plan (100 req/dia). Proibido criar loops infinitos.
* Dados DEVEM ser cacheados localmente.
* Modelo de IA para análise de jogos: **Gemini 2.0 Flash** (produção), fallback para `gemini-flash-lite`.
* Modelo de IA para SRE/Auto-Healing (Fase 5): **Gemini 1.5 Pro** (janela de 1M tokens obrigatória).

## 6. Deploy Contínuo do Frontend e Validação de UI
* Toda alteração no frontend (`web/**`) DEVE ser acompanhada de testes (`pytest tests/web/`) e publicação no Render (`python deploy_frontend.py` ou via Action).
* O deploy só é considerado concluído após verificação E2E de Status HTTP 200 e integridade dos componentes visuais em produção (`https://lay-cs-baltazar.onrender.com`).

## 7. Verificação Real da Pipeline de Injeção (Mundo Real / Nuvem)
* **OBRIGATÓRIO:** Testes locais na máquina de desenvolvimento NÃO validam o fluxo final de integração contínua.
* Qualquer alteração em fluxos de agentes, scripts de injeção ou em `.github/workflows/daily_injection.yml` EXIGE que a validação seja executada DIRETAMENTE na infraestrutura do GitHub Actions (via `push` ou `workflow_dispatch`).
* Você deve monitorar os logs reais da cloud (via painel do GitHub ou API). O serviço só é declarado "pronto" após provar que a esteira roda de ponta a ponta, usando variáveis e infraestrutura do mundo real.

## 8. Integridade do Banco de Dados em Produção
* **PROIBIÇÃO ESTRITA:** O agente NUNCA deve executar `DELETE`, `DROP` ou `TRUNCATE` em produção.
* Toda correção deve ser feita via `UPDATE` aditivo.

---

## 9. Arquitetura Agêntica — Estado Atual e Regras

### Fase Ativa Atual: FASE 0 (Pré-Agêntica)
A implementação deve ser sequencial. Nunca pular fases.

| Fase | Nome | Status |
|---|---|---|
| Fase 1 | O Conselheiro Silencioso | 🔴 Não iniciada |
| Fase 2 | O Comitê de Decisão | 🔴 Não iniciada |
| Fase 3 | Tool-Calling Dinâmico | 🔴 Não iniciada |
| Fase 4 | Injeção Resiliente (ReAct) | 🔴 Não iniciada |
| Fase 5 | Auto-Healing SRE (GitHub) | 🔴 Não iniciada |

### Regras para Implementação de Agentes
1. Antes de implementar qualquer Fase, ler `docs/plano_migracao_agentica.md`.
2. Cada Fase deve poder ser desativada via variável de ambiente sem quebrar as anteriores.
3. **Degradação Graciosa:** Falha em qualquer fase ativa o comportamento da fase anterior, nunca travamento total.
4. **Guardrails financeiros:** Limites de Stake são `hardcoded` em `config.py` e NUNCA sobrescritos por lógica de agente.
5. **Proibição de `DELETE/DROP` via Agente:** Credenciais de agentes possuem apenas `SELECT/INSERT/UPDATE` (RLS no Supabase).
6. **BTTS obrigatório:** Todo agente que analisa um jogo para Lay CS deve receber a odd de BTTS SIM. Sem ela, o jogo não pode ser resgatado.

### Cascata de Captura de Odds (Match Odds + BTTS — mesma ordem para ambos)
1. **The Odds API** → `GET /v4/odds/?markets=h2h,btts`
2. **API-Football** → `GET /v3/odds?fixture={id}`
3. **Sofascore API** → `GET api.sofascore.com/api/v1/event/{id}/odds/1/all`
4. **OddsPortal (Playwright)** → Navegar até a partida e extrair DOM
5. Falha total → `odds_source: "unavailable"` → jogo excluído da análise agêntica

# Análise Crítica e Recomendações

## 🔬 Análise Crítica do Projeto

**Pontos Fortes**:
- Estrutura de testes sólida com camadas unitárias, integração e UI.
- Integração já existente com Gemini 2.0 Flash para análise de jogos.
- Pipeline de injeção usando a API do LayBack já funciona.
- Regras de proteção financeira e circuito‑breaker bem definidas.

**Principais Lacunas**:
1. **Fase 0 de Saneamento** – Captura de `match_odd`, `btts_odd` e dados de H2H/standings ainda não está garantida; o scanner pode gerar `None` e quebrar o agente.
2. **Contrato de Dados** – Falta um `MatchContext` tipado; os agentes podem divergir nos nomes dos campos.
3. **Cobertura de Dados da Fase 1** – Ainda não há implementação de BTTS, H2H e Must‑Win; três dos cinco fatores do agente Olheiro estão ausentes.
4. **Estratégia de Testes** – Testes atuais não cobrem a lógica de decisão do agente nem o fluxo completo de veredito; ausência de testes de contrato de veredito pode gerar regressões silenciosas.
5. **Smoke Test no CI** – O workflow `daily_injection.yml` ainda não tem um passo de smoke‑test antes da injeção, risco de deploys quebrados.

**Conclusão** – O plano está pronto para iniciar a **Fase 0** (saneamento) e a **Fase 1** (resgate de partidas rejeitadas), mas as fases 3‑5 precisam de detalhamento adicional antes da implementação.

## 🤖 Recomendação de Modelo de IA

| Camada | Modelo Recomendado | Motivo |
|---|---|---|
| Análise de jogos (Fase 1‑2) | **Gemini 2.0 Flash** | Rápido, barato, boa saída JSON, já integrado.
| Tool‑Calling e decisão complexa (Fase 3) | **Gemini 2.5 Pro** | Suporte nativo a chamadas de funções e maior capacidade de raciocínio.
| Leitura de logs / Auto‑Healing (Fase 5) | **Gemini 1.5 Pro** | Janela de 1 M tokens para analisar logs completos e código.
| Navegação Web / captura de odds (fallback) | **Gemini 2.0 Flash** | Multimodal suficiente para extrair dados de screenshots ou HTML.

**Alternativas** – Caso Gemini fique indisponível, considerar `Claude 3.5 Haiku` para fases 1‑4 e `Claude 3.5 Sonnet` para a fase 5.

**Próximos Passos**:
1. Copiar o plano para `docs/plano_migracao_agentica.md` no repositório.
2. Definir o `MatchContext` (TypedDict ou dataclass) e atualizar o scanner/analista.
3. Implementar a Fase 0 de saneamento de dados e atualizar os mocks de teste.
4. Inserir o smoke‑test no workflow CI.
5. Revisar a alocação de quota de APIs (Odds, BTTS) antes de iniciar a coleta em produção.

*Esta atualização reflete as informações solicitadas e inclui a análise crítica e a recomendação de modelo.*
# Análise Crítica e Recomendações

## 🔬 Análise Crítica do Projeto

**Pontos Fortes**:
- Estrutura de testes sólida com camadas unitárias, integração e UI.
- Integração já existente com Gemini 2.0 Flash para análise de jogos.
- Pipeline de injeção usando a API do LayBack já funciona.
- Regras de proteção financeira e circuito‑breaker bem definidas.

**Principais Lacunas**:
1. **Fase 0 de Saneamento** – Captura de `match_odd`, `btts_odd` e dados de H2H/standings ainda não está garantida; o scanner pode gerar `None` e quebrar o agente.
2. **Contrato de Dados** – Falta um `MatchContext` tipado; os agentes podem divergir nos nomes dos campos.
3. **Cobertura de Dados da Fase 1** – Ainda não há implementação de BTTS, H2H e Must‑Win; três dos cinco fatores do agente Olheiro estão ausentes.
4. **Estratégia de Testes** – Testes atuais não cobrem a lógica de decisão do agente nem o fluxo completo de veredito; ausência de testes de contrato de veredito pode gerar regressões silenciosas.
5. **Smoke Test no CI** – O workflow `daily_injection.yml` ainda não tem um passo de smoke‑test antes da injeção, risco de deploys quebrados.

**Conclusão** – O plano está pronto para iniciar a **Fase 0** (saneamento) e a **Fase 1** (resgate de partidas rejeitadas), mas as fases 3‑5 precisam de detalhamento adicional antes da implementação.

## 🤖 Recomendação de Modelo de IA

| Camada | Modelo Recomendado | Motivo |
|---|---|---|
| Análise de jogos (Fase 1‑2) | **Gemini 2.0 Flash** | Rápido, barato, boa saída JSON, já integrado.
| Tool‑Calling e decisão complexa (Fase 3) | **Gemini 2.5 Pro** | Suporte nativo a chamadas de funções e maior capacidade de raciocínio.
| Leitura de logs / Auto‑Healing (Fase 5) | **Gemini 1.5 Pro** | Janela de 1 M tokens para analisar logs completos e código.
| Navegação Web / captura de odds (fallback) | **Gemini 2.0 Flash** | Multimodal suficiente para extrair dados de screenshots ou HTML.

**Alternativas** – Caso Gemini fique indisponível, considerar `Claude 3.5 Haiku` para fases 1‑4 e `Claude 3.5 Sonnet` para a fase 5.

**Próximos Passos**:
1. Copiar o plano para `docs/plano_migracao_agentica.md` no repositório.
2. Definir o `MatchContext` (TypedDict ou dataclass) e atualizar o scanner/analista.
3. Implementar a Fase 0 de saneamento de dados e atualizar os mocks de teste.
4. Inserir o smoke‑test no workflow CI.
5. Revisar a alocação de quota de APIs (Odds, BTTS) antes de iniciar a coleta em produção.

*Esta atualização reflete as informações solicitadas e inclui a análise crítica e a recomendação de modelo.*
