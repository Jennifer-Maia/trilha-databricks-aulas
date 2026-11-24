---
description: Aula 6 · comando 02 — cria e publica o painel da Marina (dashboard AI/BI) em cima da gold
allowed-tools: Bash(python3 modulo-01-analytics-engineering/aula-06-validar-e-publicar/scripts/criar_painel.py:*), Read
---

Responda em português do Brasil, simples e curto.

1. Leia `modulo-01-analytics-engineering/aula-06-validar-e-publicar/meu-portfolio/CONTEXTO.md` e siga as regras dele. Se não existir, diga para rodar `/aula06-01-contexto` primeiro e pare.
2. Rode `python3 modulo-01-analytics-engineering/aula-06-validar-e-publicar/scripts/criar_painel.py`.
3. Explique em até 5 linhas, sem jargão:
   - o painel lê só `gold.vendas_por_regiao` (o que o contrato define como saída);
   - tem 3 números (pedidos, valor, ticket médio), vendas por região, vendas por mês e um filtro de região;
   - foi publicado **sem credencial embutida**: cada pessoa vê com o próprio acesso, então o filtro da aula 5 (RN-08) continua valendo. Com credencial embutida, todo mundo veria o que quem publicou vê;
   - o link para abrir (está na saída do script).
4. Peça para o aluno abrir o link, conferir que o total de pedidos é **1.052** e tirar um print para o portfólio (salvar em `meu-portfolio/prints/painel.png`).

Se o aluno pedir para mudar o painel (um visual novo, outra cor), edite `scripts/painel_marina.json` mantendo as regras: só a tabela `vendas_por_regiao` sem catálogo no `FROM`, nenhum número fora do contrato. Depois rode o script de novo: ele atualiza o mesmo painel, não cria outro.
