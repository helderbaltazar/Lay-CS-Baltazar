# Automação Lay Correct Score — Plano v3

Scanner diário que rankeia os jogos do dia por **menor probabilidade** dos placares 0×1, 0×2, 0×3 e 1×3, exibindo os resultados em uma **página web interativa**.

---

## ✅ Decisões Confirmadas

| Item | Decisão |
|---|---|
| **Objetivo** | Ranking de jogos por menor probabilidade de cada placar-alvo |
| **Placares-alvo** | Lay 0×1, Lay 0×2, Lay 0×3, Lay 1×3 |
| **Modelo** | Poisson + correção Dixon-Coles |
| **Dados** | API-Football (fixtures + stats de times) |
| **API Key** | `a560c...1cc9` (Free: 100 req/dia, seasons 2022-2024) |
| **Saída** | Página web local (HTML/CSS/JS + Flask) |
| **Ligas** | 23 ligas/copas principais |
| **Sem cálculo de odds/EV** | O modelo gera apenas probabilidades estatísticas |
| **Agendamento** | Tarefa automática diária às 00:00 e 01:00 (Brasília) |
| **Banco de Dados (Histórico)** | SQLite + SQLAlchemy ORM (preparado para migração na nuvem alterando apenas 1 linha) |
| **Repositório** | [GitHub - Lay-CS-Baltazar](https://github.com/helderbaltazar/Lay-CS-Baltazar) |

---

## 🔒 Segurança e Preparação para Nuvem (Cloud-Ready)

Para garantir que a transição para um servidor na nuvem (VPS, AWS, Heroku) seja segura, as seguintes práticas são obrigatórias desde o dia 1:

1. **Gestão de Segredos (Variáveis de Ambiente):**
   - **NENHUMA** chave de API, senha de banco de dados ou `SECRET_KEY` do Flask será escrita (hardcoded) no código.
   - Usaremos a biblioteca `python-dotenv`. Todas as credenciais ficarão em um arquivo local `.env` (que nunca será comitado).
   - Um arquivo `.env.example` vazio será mantido no repositório para documentar quais variáveis são necessárias.

2. **Isolamento de Dados Sensíveis (Git):**
   - O arquivo do banco de dados (`database.sqlite3`), logs e o arquivo `.env` estão estritamente bloqueados pelo `.gitignore`. Isso impede vazamento de dados estratégicos e chaves em repositórios públicos/privados.

3. **Segurança Web (Flask):**
   - O modo `debug=True` do Flask só será usado em desenvolvimento. Em produção, será desativado para evitar execução arbitrária de código.
   - O servidor web só será exposto para a rede externa (`0.0.0.0`) quando estiver protegido por um proxy reverso (como Nginx) ou Gunicorn. Localmente, rodará apenas em `127.0.0.1`.

---

## Lógica do Sistema

```
  ┌─────────────────────────────────────────────┐
  │  SCHEDULER (APScheduler)                    │
  │  Cron: 00:00 e 01:00 BRT (diário)          │
  │  Também: ao iniciar o servidor              │
  └──────────────────┬──────────────────────────┘
                     │ dispara
                     ▼
        API-Football (fixtures do dia)
                     │
                     ▼
          Jogos das ligas principais
                     │
                     ▼
        API-Football (stats de cada time) ──► Cache local (7 dias)
                     │
                     ▼
          Calcular λ_home e λ_away (gols esperados)
                     │
                     ▼
          Modelo Poisson + Dixon-Coles
                     │
                     ▼
          Matriz de probabilidades de todos os placares
                     │
                     ▼
          Extrair prob. dos placares-alvo (0×1, 0×2, 0×3, 1×3)
                     │
                     ▼
          Rankear por menor probabilidade
                     │
                     ▼
          Salvar resultado em JSON ──► Página web lê automaticamente
```

### Por que funciona para Lay CS?
- **Lay = apostar CONTRA** o placar acontecer
- Quanto **menor a probabilidade** do placar → **maior a chance do lay ganhar**
- O modelo identifica jogos onde o perfil dos times torna certos placares **estatisticamente improvváveis**
- Ex: Time com λH alto (ataque forte em casa) + visitante com λA baixo (ataque fraco fora) → probabilidade muito baixa de 0×1, 0×2, 0×3

### Por que dois horários de execução?
- **00:00 BRT** — Captura os jogos do novo dia assim que a data vira. Ao acordar, os dados já estarão prontos na página.
- **01:00 BRT** — Segunda execução como segurança. Algumas fixtures podem ser publicadas/atualizadas pela API com atraso. Garante que jogos adicionados após a meia-noite sejam incluídos.

---

## 🏆 Ligas e Copas Cobertas (23)

| Liga | ID | País |
|---|---|---|
| Premier League | 39 | 🏴 Inglaterra |
| La Liga | 140 | 🇪🇸 Espanha |
| Serie A | 135 | 🇮🇹 Itália |
| Bundesliga | 78 | 🇩🇪 Alemanha |
| Ligue 1 | 61 | 🇫🇷 França |
| Primeira Liga | 94 | 🇵🇹 Portugal |
| Eredivisie | 88 | 🇳🇱 Holanda |
| Jupiler Pro League | 144 | 🇧🇪 Bélgica |
| Super Lig | 203 | 🇹🇷 Turquia |
| Saudi Pro League | 307 | 🇸🇦 Arábia Saudita |
| Brasileirão Série A | 71 | 🇧🇷 Brasil |
| Brasileirão Série B | 72 | 🇧🇷 Brasil |
| Liga Profesional | 128 | 🇦🇷 Argentina |
| Liga MX | 262 | 🇲🇽 México |
| MLS | 253 | 🇺🇸 EUA |
| Champions League | 2 | 🇪🇺 Europa |
| Europa League | 3 | 🇪🇺 Europa |
| Conference League | 848 | 🇪🇺 Europa |
| Copa Libertadores | 13 | 🌎 América do Sul |
| Copa Sudamericana | 11 | 🌎 América do Sul |
| Copa do Brasil | 73 | 🇧🇷 Brasil |
| World Cup | 1 | 🌍 Mundial |
| Copa América | 15 | 🌎 América do Sul |

---

## Proposed Changes

### Estrutura do Projeto

```
Automação Lay CS/
├── config.py                   # Configurações gerais
├── main.py                     # Ponto de entrada
├── scheduler.py                # Agendador de tarefas (cron diário)
├── database/
│   ├── __init__.py
│   ├── db.py                   # Conexão SQLAlchemy e engine (SQLite default)
│   └── models_db.py            # Schemas das tabelas (Matches, Predictions)
├── models/
│   ├── __init__.py
│   └── poisson.py              # Poisson + Dixon-Coles
├── data/
│   ├── __init__.py
│   ├── api_football.py         # Coleta via API-Football
│   ├── cache.py                # Cache local de stats
│   └── league_config.py        # IDs das ligas + médias + mapeamentos
├── analysis/
│   ├── __init__.py
│   ├── scanner.py              # Scanner + ranking
│   └── resolver.py             # Busca placares finais e atualiza greens/reds
├── web/
│   ├── app.py                  # Servidor Flask
│   ├── templates/
│   │   ├── index.html          # Página principal (Scanner do dia)
│   │   └── dashboard.html      # Dashboard Histórico (Win rate, gráficos)
│   └── static/
│       ├── style.css           # Estilos (tema escuro)
│       └── script.js           # Filtros, sort, interatividade
├── tests/                      # Suíte de testes automatizados
│   ├── conftest.py             # Fixtures compartilhadas (pytest)
│   ├── unit/                   # Testes unitários
│   │   ├── test_poisson.py     # Testes do modelo Poisson + Dixon-Coles
│   │   ├── test_scanner.py     # Testes do scanner e ranking
│   │   ├── test_cache.py       # Testes do cache
│   │   ├── test_league_config.py
│   │   └── test_db.py          # Testes das operações do banco de dados
│   ├── integration/            # Testes de integração (com mocks de API)
│   │   ├── test_api_football.py
│   │   ├── test_scheduler.py
│   │   ├── test_resolver.py    # Teste de atualização de resultados (Green/Red)
│   │   └── test_full_pipeline.py
│   ├── web/                    # Testes da interface web
│   │   └── test_app.py
│   └── fixtures/               # Dados de teste estáticos
│       ├── api_fixtures_response.json
│       ├── api_team_stats_response.json
│       └── expected_rankings.json
├── data_store/                 # Armazenamento persistente local
│   └── database.sqlite3        # Banco de Dados (Substitui os arquivos JSON espalhados)
├── logs/                       # Logs do scheduler
│   └── scheduler.log
├── cache/                      # Cache de stats de times
│   └── team_stats.json
├── requirements.txt
├── .env                        # [NÃO COMITADO] Variáveis de ambiente (ex: chaves API)
├── .env.example                # Template vazio das variáveis necessárias
├── pytest.ini                  # Configuração do pytest
└── README.md
```

---

### 1. Configuração

#### [NEW] [config.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/config.py)
- **Segurança:** Usa `os.getenv()` e `python-dotenv` para carregar `API_KEY` do arquivo `.env`.
- Placares-alvo: `[(0,1), (0,2), (0,3), (1,3)]`
- Parâmetro ρ (rho) Dixon-Coles: `-0.10`
- Número máximo de gols na matriz: `7`
- Porta do servidor web: `5000`
- Diretório de cache, results e logs
- Horários do cron: `['00:00', '01:00']` (timezone `America/Sao_Paulo`)

---

### 2. Modelo Estatístico

#### [NEW] [models/poisson.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/models/poisson.py)

Classe `PoissonDixonColes`:
- **`__init__(rho=-0.10, max_goals=7)`**
- **`poisson_pmf(k, lam)`** — P(X=k) dado λ
- **`dixon_coles_tau(h, a, lam_h, lam_a)`** — Fator de correção τ para placares baixos (0-0, 1-0, 0-1, 1-1)
- **`predict(lam_home, lam_away)`** — Retorna matriz completa de probabilidades normalizada
- **`get_probabilities(lam_home, lam_away, targets)`** — Retorna dict `{(0,1): 0.0567, (0,2): 0.0272, ...}` para os placares-alvo

---

### 3. Dados

#### [NEW] [data/league_config.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/data/league_config.py)
- Dicionário `MAIN_LEAGUES`: ID → nome, país, bandeira
- Dicionário `LEAGUE_AVERAGES`: ID → `(avg_home_goals, avg_away_goals)` — médias históricas de gols por liga
- Dicionário `DOMESTIC_LEAGUE_MAP`: Para times que jogam em copas (Champions, Libertadores, Copa do Brasil), mapeia `team_id → league_id` da liga doméstica para buscar stats
- Função `get_league_avg(league_id)` — retorna médias com fallback para valores default

#### [NEW] [data/api_football.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/data/api_football.py)
- **`get_fixtures(date, timezone='America/Sao_Paulo')`** — Busca todos os jogos do dia (1 request)
- **`filter_main_leagues(fixtures)`** — Filtra apenas ligas configuradas
- **`get_team_stats(team_id, league_id, season=2024)`** — Stats de um time (com fallback para 2023, 2022)
- **`get_team_domestic_league(team_id, competition_id)`** — Resolve liga doméstica para times em copas
- Rate limiting: `time.sleep(0.3)` entre requests
- Tratamento de erros da API

#### [NEW] [data/cache.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/data/cache.py)
- Cache em arquivo JSON local (`cache/team_stats.json`)
- **`get(key)`** — Retorna dados se existem e não expiraram
- **`set(key, value, ttl_days=7)`** — Salva com timestamp
- **`is_valid(key)`** — Verifica se cache está válido
- Evita requests duplicados para o mesmo time (crucial com 100 req/dia)

---

### 4. Scanner e Ranking

#### [NEW] [analysis/scanner.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/analysis/scanner.py)

- **`calculate_lambdas(home_stats, away_stats, league_avg)`** — Calcula λ_home e λ_away usando forças relativas de ataque/defesa
- **`scan_match(fixture, model, targets)`** — Analisa um jogo, retorna probabilidades dos placares-alvo
- **`scan_all(fixtures, model)`** — Analisa todos os jogos do dia
- **`rank_by_target(results)`** — Gera 4 rankings separados (um por placar-alvo), ordenados por menor probabilidade
- **`save_to_db(rankings)`** — Salva as predições e informações da partida no Banco de Dados (substituindo a antiga persistência em JSON local).

---

### 5. Banco de Dados e Histórico (SQLAlchemy)

#### [NEW] [database/db.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/database/db.py)
- Engine de conexão: `sqlite:///data_store/database.sqlite3`
- SessionMaker central.

#### [NEW] [database/models_db.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/database/models_db.py)
Duas tabelas relacionais usando `declarative_base`:

1. **`Match`**
   - `id` (PK)
   - `fixture_id` (ID da API, unique)
   - `date` (DateTime)
   - `league_name`, `home_team`, `away_team`
   - `status` (NS, FT, etc)
   - `real_score` (ex: "0-1" ou None se pendente)

2. **`Prediction`**
   - `id` (PK)
   - `match_id` (FK -> Match.id)
   - `target_score` (ex: '0-1')
   - `probability` (Float)
   - `rank` (Integer)
   - `is_hit` (Boolean, default None) -> `True` se o placar alvo NÃO aconteceu (Green no Lay), `False` se aconteceu (Red).

#### [NEW] [analysis/resolver.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/analysis/resolver.py)
- **`resolve_pending_matches(date)`**: Busca no banco todos os jogos de ontém cujo `status` não é `FT`.
- Chama a API-Football `GET /fixtures?date={ontem}` (apenas 1 request).
- Atualiza a tabela `Match` com o `real_score` e `status`.
- Atualiza a tabela `Prediction` calculando o `is_hit`.

---

### 6. Agendador de Tarefas

#### [NEW] [scheduler.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/scheduler.py)

Usa a biblioteca **APScheduler** para agendar a execução automática do scanner.

- **Três jobs diários** configurados via `CronTrigger`:
  - **Job 1 — 00:00 BRT:** Busca fixtures do novo dia e gera o ranking (Scanner).
  - **Job 2 — 01:00 BRT:** Re-executa o scanner como segurança.
  - **Job 3 — 04:00 BRT:** Executa o `resolver.py` para atualizar os resultados reais dos jogos de ontém e fechar as predições (marcar Greens/Reds).
- **Timezone:** `America/Sao_Paulo` (Brasília)
- **Função `run_daily_scan(date=None)`:**
  1. Determina a data (hoje se `None`)
  2. Executa o scanner completo
  3. Salva resultados em `results/{date}.json`
  4. Loga execução em `logs/scheduler.log`
- **Integração com Flask:** O scheduler roda como **thread em background** dentro do processo do servidor Flask (via `BackgroundScheduler`), sem precisar de processo separado
- **Execução ao iniciar:** Ao subir o servidor, executa imediatamente um scan se ainda não existir resultado para o dia atual
- **Logging:** Registra em `logs/scheduler.log`:
  - Horário de cada execução
  - Número de jogos encontrados/analisados
  - Erros da API (se houver)
  - Requests utilizados

```python
# Exemplo de configuração do scheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

scheduler = BackgroundScheduler(timezone=pytz.timezone('America/Sao_Paulo'))

# Job 1: meia-noite
scheduler.add_job(
    run_daily_scan,
    CronTrigger(hour=0, minute=0, timezone='America/Sao_Paulo'),
    id='scan_midnight',
    name='Scanner meia-noite',
    replace_existing=True
)

# Job 2: uma da manhã
scheduler.add_job(
    run_daily_scan,
    CronTrigger(hour=1, minute=0, timezone='America/Sao_Paulo'),
    id='scan_1am',
    name='Scanner 01:00',
    replace_existing=True
)

scheduler.start()
```

---

### 7. Interface Web

#### [NEW] [web/app.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/web/app.py)
- Servidor Flask na porta 5000
- Integra o scheduler (APScheduler roda em background)
- `GET /` — Página principal com dados do dia buscando no banco (Matches e Predictions)
- `GET /history` — Renderiza o dashboard de resultados passados com Win Rate
- `GET /api/scan` — Executa scanner manualmente
- `GET /api/resolve` — Roda o resolver.py manualmente para conferir greens/reds
- `GET /api/status` — Status do scheduler

#### [NEW] [web/templates/index.html](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/web/templates/index.html)
- Tabela de jogos do dia agrupada por placar-alvo (igual a POC, lendo do BD).

#### [NEW] [web/templates/dashboard.html](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/web/templates/dashboard.html)
- **Histórico e Win Rate:**
  - Placar 0x1: Acertou X de Y jogos (Z%)
  - Placar 0x2: Acertou X de Y jogos (Z%)
- Tabela paginada com os jogos passados, mostrando a Previsão (probabilidade, odd estimada) x Resultado Real.
- Jogos `Green` marcados em verde, `Red` em vermelho escuro.

#### [NEW] [web/static/style.css](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/web/static/style.css)
- **Tema escuro** estilo terminal de trading
- Cores: fundo `#1a1a2e`, cards `#16213e`, destaque `#0f3460`, texto `#e0e0e0`
- Top 3 de cada ranking com borda verde gradiente

#### [NEW] [web/static/script.js](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/web/static/script.js)
- Filtros dinâmicos, charts simples se necessário (via Chart.js).

---

### 8. Script Principal

#### [NEW] [main.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/main.py)

#### [NEW] [requirements.txt](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/requirements.txt)
```
flask
requests
APScheduler
pytz
SQLAlchemy
python-dotenv
pytest
pytest-cov
```

#### [NEW] [README.md](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/README.md)
- Como configurar a API key via `.env`
- Como migrar o banco de dados futuramente
- Como executar localmente
- Instruções de Deploy na Nuvem (Variáveis de Ambiente vs `.env`)

---

## Gestão de Quota da API (100 req/dia)

| Operação | Requests | Quando |
|---|---|---|
| Fixtures do dia (Scanner) | 1 | 00:00 e 01:00 |
| Fixtures de ontém (Resolver) | 1 | 04:00 |
| Stats por time (2 por jogo) | 2 × N | Só se não está em cache |

---

### Procedimento de Rollback

#### Rollback rápido (voltar para a versão anterior)
```bash
# Ver todas as versões disponíveis
git tag -l

# Voltar para uma versão específica (ex: v0.3.0)
git checkout v0.3.0

# Se quiser DESCARTAR tudo que veio depois e voltar permanentemente
git checkout v0.3.0
git checkout -b rollback-v0.3.0
git branch -D main
git branch -m main
```

#### Rollback cirúrgico (desfazer só o último commit)
```bash
# Desfazer o último commit mantendo os arquivos modificados
git reset --soft HEAD~1

# Desfazer o último commit E as mudanças nos arquivos
git reset --hard HEAD~1
```

#### Comparar versões (diagnóstico)
```bash
# Ver o que mudou entre duas versões
git diff v0.2.0 v0.3.0

# Ver o que mudou em um arquivo específico
git diff v0.2.0 v0.3.0 -- models/poisson.py

# Ver o histórico completo
git log --oneline --tags
```

---

### Regras de Commit

| Regra | Motivo |
|---|---|
| **1 commit por etapa de implementação** | Cada commit = 1 ponto de rollback limpo |
| **Mensagem sempre começa com a versão** | Ex: `v0.3.0: Scanner de jogos + ranking` |
| **Nunca commitar com testes falhando** | Toda tag/commit é um estado estável |
| **Tag em toda versão MINOR ou MAJOR** | Rollback rápido via `git checkout <tag>` |
| **Commits intermediários permitidos sem tag** | Ex: `wip: rascunho do scanner` (sem tag, pode ser squashed) |

---

### Arquivo de Versão

#### [NEW] [version.py](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/version.py)
```python
__version__ = "0.1.0"
```

---

### `.gitignore`

#### [NEW] [.gitignore](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/.gitignore)
```
# Segurança (Nunca comitar credenciais)
.env

# Banco de Dados e Cache (Não versionar dados reais)
data_store/*.sqlite3
cache/
logs/
results/

# Python
__pycache__/
*.pyc
.pytest_cache/

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

> [!WARNING]
> Os diretórios `cache/`, `results/` e `logs/` **não são versionados** — são dados gerados em runtime. Isso garante que o rollback via Git não sobrescreva dados reais de produção.

## Metodologia de Desenvolvimento (Looping & Contexto)

Para garantir estabilidade e evitar perda de contexto ao longo do desenvolvimento, adotaremos as seguintes práticas:

### 1. Looping Engineering (TDD Autônomo)
O desenvolvimento será feito em ciclos iterativos curtos (loops de feedback):
1. Escrever/Atualizar Teste Unitário.
2. Escrever Código da Funcionalidade.
3. Executar Teste no Terminal.
4. Analisar Erros (se houver) e corrigir autonomamente até o teste passar.
5. Fazer o Commit da versão no Git.
*Somente após fechar o loop com sucesso avançaremos para a próxima etapa.*

### 2. Gestão de Contexto (Context Preservation)
Para evitar "esquecimento" (estouro de context window) em sessões longas:
- **`PROJECT_CONTEXT.md`**: Um arquivo na raiz do projeto servirá como "memória de longo prazo". Conterá regras de negócio, chaves de API, estado atual e decisões críticas. O agente lerá este arquivo obrigatoriamente se perder o contexto.
- **`task.md`**: Documento de checklist mantido nos artefatos do agente, marcando o status exato de progresso (`[ ]` pendente, `[/]` em andamento, `[x]` concluído).
- **Subagents**: Tarefas muito longas de pesquisa ou debug isolado serão delegadas a subagentes para preservar o contexto da conversa principal.

---

## Estratégia de Testes e Proteção Contra Regressão

> [!IMPORTANT]
> **Regra de ouro:** Nenhuma funcionalidade nova é considerada pronta até que (1) seus próprios testes passem e (2) **todos os testes existentes continuem passando**. O comando `python -m pytest tests/ -v` deve ser executado após cada alteração.

### Filosofia

```
Nova funcionalidade → Escrever testes da funcionalidade → Rodar TODOS os testes → Tudo verde? → Merge
                                                              │
                                                          Algum vermelho?
                                                              │
                                                         Corrigir antes de prosseguir
```

---

### Estrutura dos Testes

```
tests/
├── conftest.py                    # Fixtures compartilhadas do pytest
├── unit/                          # Rápidos, sem I/O, sem rede
│   ├── test_poisson.py            # Modelo matemático
│   ├── test_scanner.py            # Lógica de ranking
│   ├── test_cache.py              # Cache local
│   └── test_league_config.py      # Configurações de ligas
├── integration/                   # Com mocks, testam fluxo entre módulos
│   ├── test_api_football.py       # API com responses mockadas
│   ├── test_scheduler.py          # Jobs agendados
│   └── test_full_pipeline.py      # Fluxo completo fixture → ranking
├── web/                           # Endpoints Flask
│   └── test_app.py                # GET /, /api/scan, /api/status
└── fixtures/                      # Dados estáticos para testes (JSON)
    ├── api_fixtures_response.json
    ├── api_team_stats_response.json
    └── expected_rankings.json
```

---

### 1. Testes Unitários (`tests/unit/`)

**Sem rede, sem I/O, sem dependências externas.** Rodam em milissegundos.

#### [NEW] `test_poisson.py` — Modelo Matemático
| Teste | O que valida |
|---|---|
| `test_poisson_pmf_known_values` | P(k=0, λ=1) ≈ 0.3679, P(k=1, λ=1) ≈ 0.3679, etc. |
| `test_poisson_pmf_zero_lambda` | λ=0 → P(0)=1.0, P(k>0)=0.0 |
| `test_matrix_sums_to_one` | Soma de todas as probabilidades na matriz ≈ 1.0 (tolerância 0.001) |
| `test_matrix_symmetry` | Se λH=λA, então P(1-0) = P(0-1) |
| `test_dixon_coles_adjusts_low_scores` | Com ρ<0, P(0-0) e P(1-1) devem ser maiores que no Poisson puro |
| `test_dixon_coles_no_effect_high_scores` | τ=1.0 para placares ≥ 2 gols (sem alteração) |
| `test_home_advantage_effect` | λH > λA → P(1-0) > P(0-1) |
| `test_strong_home_low_away_prob` | λH=3.0, λA=0.5 → P(0-1) < 2% |
| `test_get_probabilities_returns_targets` | Retorna exatamente os placares solicitados |

#### [NEW] `test_scanner.py` — Scanner e Ranking
| Teste | O que valida |
|---|---|
| `test_calculate_lambdas_basic` | Ataque=1.5, defesa=0.8, liga_avg=1.3 → λ calculado corretamente |
| `test_calculate_lambdas_bounds` | λ nunca < 0.2 e nunca > 5.0 |
| `test_rank_ascending_order` | Ranking está em ordem crescente de probabilidade |
| `test_rank_four_targets` | Gera exatamente 4 rankings (um por placar-alvo) |
| `test_scan_match_returns_all_fields` | Resultado contém home, away, league, lambdas, probabilities |
| `test_scan_empty_fixtures` | Lista vazia → retorna rankings vazios sem erro |
| `test_scan_missing_stats` | Time sem stats → excluído do ranking sem crash |
| `test_save_and_load_results` | Salvar em JSON e recarregar produz dados idênticos |

#### [NEW] `test_cache.py` — Cache Local
| Teste | O que valida |
|---|---|
| `test_set_and_get` | Salvar e recuperar um valor |
| `test_expired_cache` | Item com TTL expirado retorna None |
| `test_valid_cache` | Item dentro do TTL retorna o valor |
| `test_cache_file_created` | Arquivo JSON é criado no disco |
| `test_cache_survives_restart` | Dados persistem entre instâncias |
| `test_cache_overwrite` | Salvar mesmo key atualiza o valor |

#### [NEW] `test_league_config.py` — Configurações
| Teste | O que valida |
|---|---|
| `test_all_leagues_have_averages` | Toda liga no MAIN_LEAGUES tem entrada em LEAGUE_AVERAGES |
| `test_averages_are_reasonable` | Médias entre 0.5 e 3.0 gols/jogo |
| `test_get_league_avg_fallback` | Liga desconhecida retorna default (1.40, 1.10) |
| `test_no_duplicate_league_ids` | Sem IDs duplicados |

---

### 2. Testes de Integração (`tests/integration/`)

**Usam mocks para simular a API.** Testam o fluxo entre módulos.

#### [NEW] `test_api_football.py` — Coleta de Dados (mockada)
| Teste | O que valida |
|---|---|
| `test_get_fixtures_parses_response` | JSON mockado da API é parseado corretamente |
| `test_filter_main_leagues` | Filtra apenas ligas configuradas, descarta o resto |
| `test_get_team_stats_fallback_season` | Se season 2024 falha, tenta 2023 e depois 2022 |
| `test_get_team_stats_uses_cache` | Segunda chamada para mesmo time não faz request |
| `test_api_error_handling` | Erro 429 (rate limit) → tratado sem crash |
| `test_api_empty_response` | API retorna 0 results → retorna None sem crash |

> **Mock:** Usar `unittest.mock.patch` para substituir `requests.get` por responses JSON estáticos salvos em `tests/fixtures/`.

#### [NEW] `test_scheduler.py` — Agendador
| Teste | O que valida |
|---|---|
| `test_scheduler_has_two_jobs` | Exatamente 2 jobs configurados |
| `test_jobs_timezone_brasilia` | Ambos os jobs usam `America/Sao_Paulo` |
| `test_jobs_correct_hours` | Job 1 às 00:00, Job 2 às 01:00 |
| `test_run_daily_scan_saves_result` | Execução do scan gera arquivo em `results/` |
| `test_run_daily_scan_logs` | Execução gera entrada no log |

#### [NEW] `test_full_pipeline.py` — Fluxo Completo (regressão principal)
| Teste | O que valida |
|---|---|
| `test_pipeline_fixtures_to_rankings` | Dado fixtures mockados + stats mockados → gera rankings corretos |
| `test_pipeline_known_match` | Cruzeiro vs Atlético-MG com stats conhecidas → probabilidades dentro de tolerância (±1%) comparadas com valores da POC |
| `test_pipeline_multiple_leagues` | Jogos de ligas diferentes processados corretamente |
| `test_pipeline_result_structure` | JSON de saída contém todos os campos esperados |
| `test_pipeline_rankings_consistency` | Mesmo input → mesmo output (determinístico) |

> [!IMPORTANT]
> **`test_pipeline_known_match`** é o teste mais importante de regressão. Ele usa os valores exatos da POC (Cruzeiro vs Atlético-MG, 25/08/2026) como baseline. Se qualquer alteração no modelo mudar essas probabilidades além da tolerância, o teste falha.

---

### 3. Testes Web (`tests/web/`)

#### [NEW] `test_app.py` — Endpoints Flask
| Teste | O que valida |
|---|---|
| `test_index_returns_200` | `GET /` retorna status 200 |
| `test_index_contains_title` | HTML contém o título da página |
| `test_api_scan_returns_json` | `GET /api/scan` retorna JSON válido |
| `test_api_scan_with_date` | `GET /api/scan?date=2026-08-25` retorna dados da data |
| `test_api_status_returns_scheduler_info` | `GET /api/status` retorna próxima execução |
| `test_api_scan_no_games` | Dia sem jogos → JSON com rankings vazios |

> **Fixture pytest:** Usar `app.test_client()` do Flask para simular requests sem subir servidor real.

---

### 4. Dados de Teste Estáticos (`tests/fixtures/`)

#### [NEW] `api_fixtures_response.json`
Response mockada de `GET /fixtures?date=2026-08-25` com 12 jogos (cópia real da POC).

#### [NEW] `api_team_stats_response.json`
Stats mockadas de todos os times usados nos testes (Cruzeiro, Atlético-MG, Bodo/Glimt, etc.).

#### [NEW] `expected_rankings.json`
Rankings esperados para os dados mockados — baseline de regressão.

---

### 5. Configuração do Pytest

#### [NEW] [pytest.ini](file:///Users/macgeint/Downloads/Automação%20Lay%20CS/pytest.ini)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Testes unitários (rápidos, sem I/O)
    integration: Testes de integração (com mocks)
    web: Testes dos endpoints Flask
    regression: Testes de regressão (baseline da POC)
addopts = -v --tb=short
```

#### Dependências de teste (adicionadas ao `requirements.txt`):
```
pytest
pytest-cov
```

---

### 6. Comandos de Teste

```bash
# Rodar TODOS os testes (obrigatório antes de qualquer merge)
python -m pytest tests/ -v

# Só testes unitários (rápido, rodar durante desenvolvimento)
python -m pytest tests/unit/ -v

# Só testes de integração
python -m pytest tests/integration/ -v

# Só testes web
python -m pytest tests/web/ -v

# Só testes de regressão (baseline da POC)
python -m pytest tests/ -v -m regression

# Com relatório de cobertura
python -m pytest tests/ -v --cov=. --cov-report=term-missing
```

---

### 7. Protocolo de Desenvolvimento

Cada nova funcionalidade segue este protocolo:

```
┌──────────────────────────────────────────────────────────────┐
│ PASSO 1: Rodar todos os testes existentes (baseline verde)  │
│          python -m pytest tests/ -v                         │
│          → Todos devem passar ANTES de começar              │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ PASSO 2: Implementar a funcionalidade nova                  │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ PASSO 3: Escrever testes para a funcionalidade nova         │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ PASSO 4: Rodar TODOS os testes (novos + antigos)            │
│          python -m pytest tests/ -v                         │
│          → TODOS devem passar (novos E existentes)          │
│          → Se algum antigo quebrou → CORRIGIR antes de      │
│            prosseguir                                       │
└──────────────────────────┬───────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ PASSO 5: Funcionalidade concluída ✅                        │
└──────────────────────────────────────────────────────────────┘
```

### 8. Ordem de Implementação com Testes

Cada módulo é implementado junto com seus testes, nesta ordem:

| Etapa | Módulo | Testes Criados Junto | Testes Existentes que Devem Passar |
|---|---|---|---|
| 1 | `config.py` | — | — |
| 2 | `models/poisson.py` | `test_poisson.py` | — |
| 3 | `data/league_config.py` | `test_league_config.py` | `test_poisson` |
| 4 | `data/cache.py` | `test_cache.py` | `test_poisson`, `test_league_config` |
| 5 | `data/api_football.py` | `test_api_football.py` | todos os anteriores |
| 6 | `analysis/scanner.py` | `test_scanner.py`, `test_full_pipeline.py` | todos os anteriores |
| 7 | `scheduler.py` | `test_scheduler.py` | todos os anteriores |
| 8 | `web/app.py` + templates | `test_app.py` | todos os anteriores |
| 9 | `main.py` | — | **TODOS** (suíte completa) |

> [!CAUTION]
> **Ao final de cada etapa**, o comando `python -m pytest tests/ -v` deve resultar em **100% dos testes passando**. Se qualquer teste existente falhar após adicionar código novo, a causa da regressão deve ser identificada e corrigida antes de avançar para a próxima etapa.

---

### Manual Verification
- Rodar para jogos do dia e comparar probabilidades com intuição (times fortes em casa devem ter probabilidades baixas para 0×1)
- Conferir se top 3 faz sentido (times com ataque forte mandante)
- Validar com resultados reais após os jogos finalizarem
- Verificar que a execução agendada gera log em `logs/scheduler.log`
- Confirmar que a página web exibe dados atualizados automaticamente após a execução do cron
