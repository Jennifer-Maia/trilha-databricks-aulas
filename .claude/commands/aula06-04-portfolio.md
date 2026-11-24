---
description: Aula 6 · comando 04 — gera a ficha com números das tabelas e monta o README e o post do portfólio
allowed-tools: Bash(python3 modulo-01-analytics-engineering/aula-06-validar-e-publicar/scripts/gerar_ficha.py:*), Bash(python3 modulo-01-analytics-engineering/aula-06-validar-e-publicar/scripts/voltar_financeiro.py:*), Read, Write
---

Responda em português do Brasil, simples e curto.

1. Leia `modulo-01-analytics-engineering/aula-06-validar-e-publicar/meu-portfolio/CONTEXTO.md` e siga as regras dele. Se não existir, diga para rodar `/aula06-01-contexto` primeiro e pare.
2. Rode `python3 modulo-01-analytics-engineering/aula-06-validar-e-publicar/scripts/gerar_ficha.py`.
   - Se parar por causa do perfil, explique o "528" em uma frase, **pergunte** se pode rodar `voltar_financeiro.py` e rode a ficha de novo.
3. O script já copiou o desenho para `meu-portfolio/img/` e criou a pasta `meu-portfolio/prints/`.
4. Escreva `meu-portfolio/README.md` seguindo `docs/modelo_readme_portfolio.md`:
   - **Todo número sai de `meu-portfolio/ficha.md`**. Não invente, não arredonde diferente.
   - Inclua o desenho (`img/aula-06-projeto-ponta-a-ponta.svg`) e os prints de `prints/` se existirem (se não existirem, deixe o lugar marcado com `<!-- print do painel -->`).
   - Escreva que os dados são **fictícios**. Não cite empresa real. Não ponha links do workspace (eles só abrem com login).
   - Diga o que você **não** fez (fora do escopo do contrato), sem exagerar o que fez.
5. Escreva `meu-portfolio/post-linkedin.md` seguindo `docs/modelo_post_linkedin.md`: até 1.300 caracteres, um problema, as decisões, o resultado com números da ficha, o painel e o agente, e a frase de que os dados são fictícios.
6. Mostre o post na tela e termine com o checklist: README revisado por você, prints no lugar, post lido em voz alta antes de publicar. Lembre que a ideia é copiar a pasta `meu-portfolio/` para um repositório seu no GitHub.
