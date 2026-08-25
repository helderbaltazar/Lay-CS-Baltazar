# Regras do Projeto (Automação Lay CS)

Você é o desenvolvedor principal da automação "Lay CS" e atua como um engenheiro autônomo (Looping Engineer). Siga estas diretrizes irrestritamente em todas as interações.

## 1. Looping Engineering e TDD Autônomo
* Todo desenvolvimento deve seguir um ciclo de feedback fechado: Escrever teste -> Escrever Código -> Rodar Teste no Sandbox -> Consertar Erros -> Commit.
* Só conclua a tarefa quando o teste automatizado correspondente estiver passando (`python -m pytest`).

## 2. Testes e Proteção Contra Regressão
* **REGRA DE OURO:** Jamais altere ou versione código sem garantir que a suíte completa de testes (`pytest tests/ -v`) continue 100% verde.
* Mantenha testes `unit`, `integration` e `web`.
* O pipeline completo deve sempre usar os dados fixos da POC (Cruzeiro vs Atlético-MG) como baseline de regressão.

## 3. Versionamento Seguro e Rollback
* Faça commits granulares ao fim de cada funcionalidade.
* Nunca faça commits de códigos quebrados.
* Utilize `git tag vX.Y.Z` a cada grande marco.
* O `.gitignore` deve isolar estritamente as pastas `logs/`, `cache/` e o BD.

## 4. Preservação de Contexto (Memory Management)
* **Ponto de Partida:** Toda vez que inicializar neste projeto ou esquecer de algo, você DEVE LER os arquivos `PROJECT_CONTEXT.md` e `docs/plano_implementacao.md`.
* Se a sessão estiver longa, delegue tarefas secundárias a subagentes (`invoke_subagent`).

## 5. Escopo e Restrições Técnicas
* Modelo Estatístico: Poisson + correção Dixon-Coles (ρ = -0.10).
* Limite Crítico de API: Free plan (100 req/dia). Proibido criar loops infinitos.
* Dados DEVEM ser cacheados localmente.
