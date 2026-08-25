# Automação Lay Correct Score

Dashboard automatizado para ranqueamento diário de jogos de futebol baseando-se na **menor probabilidade** de placares exatos (Lay CS: 0x1, 0x2, 0x3, 1x3).

Utiliza o modelo estatístico de **Poisson** com ajuste de **Dixon-Coles** para identificar oportunidades onde o risco do placar-alvo acontecer é estatisticamente remoto.

> 🔒 Projeto Cloud-Ready. As credenciais são lidas via variáveis de ambiente.

## Documentação Completa
O plano de implementação completo, com arquitetura, modelagem do banco de dados e estratégias de segurança encontra-se em:
[docs/plano_implementacao.md](./docs/plano_implementacao.md)

## Requisitos Iniciais
Crie o arquivo \`.env\` (não comitado) na raiz do projeto contendo:
\`\`\`env
API_FOOTBALL_KEY=sua_chave_aqui
\`\`\`
