---
description: Aula 6 · comando 03 — cria o agente da Marina (Genie) com as regras do contrato e faz perguntas a ele
argument-hint: "[pergunta opcional]"
allowed-tools: Bash(python3 modulo-01-analytics-engineering/aula-06-validar-e-publicar/scripts/criar_agente.py:*), Read
---

Responda em português do Brasil, simples e curto.

1. Leia `modulo-01-analytics-engineering/aula-06-validar-e-publicar/meu-portfolio/CONTEXTO.md` e siga as regras dele. Se não existir, diga para rodar `/aula06-01-contexto` primeiro e pare.
2. Rode `python3 modulo-01-analytics-engineering/aula-06-validar-e-publicar/scripts/criar_agente.py`. Se o aluno passou uma pergunta (`$ARGUMENTS`), acrescente `--pergunta "<a pergunta>"`.
3. Mostre a resposta do agente e compare com a referência do `CONTEXTO.md` (1.052 pedidos, R$ 2.302.177,12). Diga se bate. Mostre também, em uma linha, que tabela o SQL do agente usou.
4. Rode de novo com `--como-vendas Sudeste --pergunta "Quanto vendemos em cada região?"`. Explique em 2 linhas: o agente roda com o acesso de quem pergunta, então no perfil vendas Sudeste ele só enxerga o Sudeste (RN-08). O script volta o perfil para financeiro no final.
5. Termine com: onde abrir o agente (link da saída), e peça um print de uma conversa para `meu-portfolio/prints/agente.png`. Próximo passo: `/aula06-04-portfolio`.

Se o agente citar uma regra errada ou der um número diferente da ficha, diga isso ao aluno: o agente ajuda, mas quem garante o número é a gold testada.
