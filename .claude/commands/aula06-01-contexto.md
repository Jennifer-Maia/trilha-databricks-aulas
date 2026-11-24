---
description: Aula 6 · comando 01 — confere o projeto e gera o contexto, as regras e os parâmetros para o Claude
argument-hint: "[perfil-da-cli] [catálogo]"
allowed-tools: Bash(databricks auth profiles:*), Bash(python3 modulo-01-analytics-engineering/aula-06-validar-e-publicar/scripts/conferir_ambiente.py:*), Bash(python3 modulo-01-analytics-engineering/aula-06-validar-e-publicar/scripts/voltar_financeiro.py:*), Read, Write
---

Você está ajudando um aluno na aula 6 do Módulo 01 (Analytics Engineering com Databricks). Responda em português do Brasil, simples e curto.

Argumentos recebidos: `$ARGUMENTS` (primeiro o perfil da Databricks CLI, depois o catálogo; o catálogo padrão é `jornada_comercial`).

1. Se o perfil não veio nos argumentos, rode `databricks auth profiles`, mostre a lista e **pergunte** qual usar. Nunca escolha sozinho.
2. Rode `python3 modulo-01-analytics-engineering/aula-06-validar-e-publicar/scripts/conferir_ambiente.py --perfil-cli <perfil> --catalogo <catálogo>`.
   - Se parar por causa do perfil (não é `financeiro`), explique o porquê em uma frase (com filtro de linha o número depende de quem consulta), **pergunte** se pode voltar para financeiro e, se o aluno disser sim, rode `voltar_financeiro.py` com os mesmos argumentos e depois o `conferir_ambiente.py` de novo.
   - Se parar por outro motivo, leia a última linha do erro e diga o que conferir (CLI sem login, catálogo errado, aulas 2 a 5 não rodadas).
3. Leia `modulo-01-analytics-engineering/aula-06-validar-e-publicar/meu-portfolio/parametros.json` e o modelo `modulo-01-analytics-engineering/aula-06-validar-e-publicar/docs/modelo_contexto_claude.md`.
4. Escreva `modulo-01-analytics-engineering/aula-06-validar-e-publicar/meu-portfolio/CONTEXTO.md` a partir do modelo, trocando `{{perfil_cli}}`, `{{catalogo}}` e `{{warehouse_id}}` pelos valores do `parametros.json`. Não mude as regras do contrato.
5. Termine com 3 linhas: o que foi conferido, onde ficou o `CONTEXTO.md` e o próximo passo (`/aula06-02-painel`).
