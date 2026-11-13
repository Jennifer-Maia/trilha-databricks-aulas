# Aula 2 · Como funciona a ingestão, peça por peça

> Guia para entender (e explicar) cada parte do lab da aula 2. Testado em 10/11/2026 num workspace Free Edition.

## A ideia em uma frase

Buscar os dados da loja numa API, página por página, e guardar as respostas **exatamente como vieram** num Volume, com um "recibo" (manifesto) que prova que veio tudo.

```
                  ┌───────────── Databricks (serverless) ─────────────┐
API Hugging Face  │  notebook aula02                                   │
/rows?offset=…    │   1. pede 100 linhas  ──► 2. confere  ──► 3. grava │──► /Volumes/<catalogo>/raw/landing/
   ▲              │        ▲   │ erro temporário? espera e repete      │      pedidos/carga_20261110_175501/
   └──────────────┼────────┘   ▼ erro nosso? para com mensagem         │        pagina_0000.json … 0014.json
                  └────────────────────────────────────────────────────┘        _manifesto.json
```

## Ordem de execução

| # | Notebook | O que faz | Tempo |
|---|---|---|---|
| 1 | `setup/01_criar_ambiente` | Cria catálogo, schemas e o Volume `raw.landing` | < 1 min |
| 2 | `exercicio/aula02_ingestao_api` (aluno) ou `solucao/aula02_ingestao_api` | Busca as 4 tabelas e grava na landing | 2 a 6 min (depende dos 429) |
| 3 | `teste/aula02_conferir_landing` | Prova que a landing está completa | < 1 min |
| — | `setup/02_plano_b_sem_api` | **Só se a API não responder.** Grava os mesmos dados, no mesmo formato | < 1 min |

Em todos, o widget `catalogo` precisa ter o mesmo valor (padrão `jornada_comercial`).

## Como rodar na mão no seu workspace

1. **Levar os arquivos para o Databricks.** O jeito mais simples é clonar este repositório como **Git folder** (Workspace → Create → Git folder). Sem Git folder: no Databricks, **Workspace → sua pasta → ⋮ → Import**, e importe os `.py` de `setup/` (do módulo) e de `exercicio/`, `solucao/` e `teste/` (desta aula). Os `.py` que começam com `# Databricks notebook source` viram notebooks.
   Para o plano B, importe também a pasta `setup/plano_b/` (os `.jsonl` e o `features.json`) **ao lado** do notebook `02_plano_b_sem_api`.
   Alternativa pelo terminal: `databricks workspace import-dir lab "/Users/<seu-email>/modulo01-lab"`.
2. **Conectar no serverless:** no topo do notebook, em *Connect*, escolha **Serverless**.
3. **Rodar célula por célula** (`Shift+Enter`) e ler a saída. Abaixo, o que cada uma mostra.

## Peça por peça

### Passo 0 · Parâmetros (widgets)
- **Widget** é a caixinha no topo do notebook. `dbutils.widgets.text("catalogo", "jornada_comercial")` cria a caixa; `dbutils.widgets.get` lê o valor.
- Por que: o mesmo código roda em `jornada_comercial` (aula) ou `jornada_teste` (ensaio) sem editar nada. A regra do lab é **nada de nome fixo no código**.
- `COLUNAS_ESPERADAS` é o contrato da fonte (seção 3 do `contrato_de_dados.md`) virando código.
- Saída esperada: `Catálogo: jornada_comercial | Dataset: trilhajornadadatabricks/loja-ficticia-jornada | Landing: /Volumes/jornada_comercial/raw/landing`

### Passo 1 · A rede deixa? (erro proposital 1)
- A Free Edition só acessa sites de uma lista não publicada ([doc](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)). Em empresa, o firewall faz o mesmo.
- Saída real em 10/11:
  ```
  IBGE (bloqueado em 09 e 10/11): SEM ACESSO → ConnectTimeout
  Hugging Face (nossa fonte): HTTP 200
  ```
- **Como explicar:** "`ConnectTimeout` = a mensagem nem chegou no servidor. Não é bug no código; é a rede. `HTTP 200` = chegou e respondeu."
- Atenção: a lista muda sem aviso. Se o IBGE responder no dia da gravação, o exemplo perde a graça. Rode essa célula antes de gravar.

### Passo 2 · A primeira chamada
- **API REST**: um endereço na internet que devolve dados (aqui em JSON) quando você faz um pedido HTTP `GET`.
- **Endpoint**: o caminho específico, aqui `/rows`.
- **Parâmetros**: o que vem depois do `?` na URL. O `requests` monta a URL a partir do dicionário `params`.
- Saída real:
  ```
  URL chamada: https://datasets-server.huggingface.co/rows?dataset=trilhajornadadatabricks%2Floja-ficticia-jornada&config=pedidos&split=train&offset=0&length=3
  Status: 200
  Chaves da resposta: ['features', 'rows', 'num_rows_total', 'num_rows_per_page', 'partial']
  Total de linhas na fonte (num_rows_total): 1500
  Colunas (features): ['order_id', 'customer_id', 'criado_em', 'itens', 'valor_bruto', 'valor_liquido']
  ```
- O `%2F` na URL é a `/` de `trilhajornadadatabricks/loja…` codificada; o `requests` faz isso sozinho.
- Cada item de `rows` = `{"row_idx": posição, "row": {o dado}, "truncated_cells": []}`.

### Erro proposital 2 · Pedir tudo de uma vez
- Saída real: `Status: 422 → {"error":"Parameter 'length' must not be greater than 100"}`
- **Como explicar:** códigos **4xx** = "o problema está no seu pedido". Tentar de novo não resolve; tem que mudar o pedido. A própria API diz o limite: 100.

### Erro proposital 3 · Esquecer de paginar
- Saída real: `Status 200 | vieram 100 de 1500 pedidos`
- **Como explicar:** o erro mais perigoso é o que **não dá erro**. HTTP 200 só diz que a chamada funcionou, não que veio tudo. Por isso guardamos `num_rows_total` e comparamos no fim.

### Passo 3 · Retry (tentar de novo)
- **Retry**: repetir a chamada quando a falha é temporária.
- **Backoff exponencial**: a espera dobra (2 s, 4 s, 8 s…) para não "metralhar" um serviço que já está com problema.
- **Rate limit (429)**: a API limita quantas chamadas cada IP faz num intervalo. Medido em 10/11 (não está documentado para o `/rows`, pode mudar): **~40 a 55 chamadas seguidas** e vem 429; libera em **~60 s**. A carga toda são 76 chamadas, então é normal ver 429 durante a aula. Por isso: 1 s de pausa entre páginas e 60 s de espera no 429.
- A doc do Hub fala de um cabeçalho `RateLimit` com o tempo até liberar ([rate limits](https://huggingface.co/docs/hub/en/rate-limits)); no `/rows` ele **não veio** nos nossos testes, mas o código usa se aparecer.
- O teste com `config: "pedido"` (sem o "s") mostra que **404 para na hora**, sem tentar de novo: `Erro definitivo HTTP 404 ... {"error":"Not found."}`.

| Código | Quem errou | Tentar de novo? |
|---|---|---|
| 200 | ninguém | — |
| 400, 404, 422 | nós (pedido errado) | não: corrigir o pedido |
| 429 | ninguém: chamadas demais | sim, depois de esperar |
| 500, 502, 503, 504 | o servidor | sim, depois de esperar |
| timeout / conexão caiu | a rede | sim, depois de esperar |

### Passo 4 · Validação de schema
- **Schema** = a lista de colunas (e tipos) que esperamos.
- Coluna **faltando** → para tudo (`ValueError`): a aula 3 quebraria ou, pior, calcularia errado. Coluna **nova** → só avisa: não quebra nada.
- Para mostrar o erro na gravação: troque `"valor_liquido"` por `"valor_liq"` em `COLUNAS_ESPERADAS` e rode a carga de `pedidos`.

### Passo 5 · O laço de paginação (`baixar_tabela`)
- **Paginação por offset**: `offset=0,length=100` → linhas 0–99; `offset=100` → 100–199; … até `offset >= num_rows_total`.
- Três decisões de projeto (e o porquê de cada uma):

| Decisão | Por quê |
|---|---|
| Grava `r.text` (resposta crua), não um JSON "arrumado" | É a prova do que a fonte mandou. Se a aula 3 tiver bug, dá para reprocessar sem chamar a API de novo |
| Uma pasta nova por carga (`carga_AAAAMMDD_HHMMSS`, hora UTC) | Nunca sobrescreve. Em 10/11, sobrescrever um arquivo e ler logo depois quebrou a leitura do Spark. Também permite auditar "o que veio em tal dia" |
| `_manifesto.json` só no fim, se o total bateu | Pasta **sem** manifesto = carga incompleta. Quem lê a landing (teste e aula 3) ignora essas pastas |

- **UTC**: horário universal (Brasília = UTC−3). Usamos UTC para não depender do fuso de quem roda.

### Passo 6 · Rodar as 4 tabelas
- Todas com o mesmo `CARGA_ID`, para saber que foram buscadas juntas.
- Saída real, resumida (no teste de 10/11 vieram três 502 e dois 429, todos superados):
  ```
  clientes: 500 linhas em 5 páginas
  produtos: 60 linhas em 1 páginas
     HTTP 502 na tentativa 1/6; nova tentativa em 2s
  pedidos: 1500 linhas em 15 páginas
     HTTP 429 (RateLimit: não informado) na tentativa 1/6; nova tentativa em 60s
  eventos_pedido: 5416 linhas em 55 páginas
  ```
- **Bom momento da aula:** se aparecer 429/502 ao vivo, não corte a gravação. É o retry funcionando.

### Passo 7 · Checkpoint com Spark
- `spark.read.json(".../pagina_*.json")` lê todas as páginas como uma tabela (uma linha por página).
- `F.explode("rows")` "abre" a lista `rows`: cada registro vira uma linha.
- `row_idx` distintos = linhas → nenhuma página repetida.
- Esperado: `clientes 500 · produtos 60 · pedidos 1500 · eventos_pedido 5416`, todos `OK`.
- Para ver os arquivos: **Catalog → jornada_comercial → raw → landing**.

## O teste (`teste/aula02_conferir_landing`)

Pega, para cada tabela, a carga completa mais recente (pela data do manifesto) e confere total, unicidade de `row_idx` e colunas. Lista as cargas sem manifesto como aviso. Termina com `assert`: se algo falhar, o notebook fica vermelho.

Saída real (com 4 cargas interrompidas por 429 durante os ensaios):
```
Aviso: eventos_pedido/carga_20261110_174341 sem manifesto (carga incompleta, ignorada)
...
Landing completa: todos os testes OK
```

## Plano B (`setup/02_plano_b_sem_api`)

Lê os `.jsonl` de `setup/plano_b/` (os mesmos arquivos publicados no Hugging Face) e grava no Volume **no formato da API**, com manifesto `"fonte": "plano_b"`. Para o resto do curso, não faz diferença de onde veio. Testado em 10/11: as 4 tabelas passam no teste.

## Glossário rápido

| Termo | Em uma frase |
|---|---|
| Volume | Pasta de arquivos governada pelo Unity Catalog (`/Volumes/catalogo/schema/volume/`) |
| Landing | Área onde os arquivos chegam como vieram, antes de qualquer tratamento |
| Manifesto | Arquivo-recibo da carga: quantas páginas e linhas, quando, de onde |
| Idempotente | Rodar de novo não estraga nada (aqui: cada carga cria pasta nova) |
| Serverless | Computação que o Databricks liga e desliga para você; a única opção na Free Edition |

## O que não foi testado

- O caminho do aluno com o repositório clonado via **Git folder** (o repositório público ainda não existe). Testei importando os arquivos para a pasta do workspace.
- A versão do aluno (`exercicio/`) só foi conferida em sintaxe: os `TODO` param com `NotImplementedError` de propósito.
- O limite do `/rows` (~40–55 chamadas, ~60 s) foi **medido**, não está na documentação. **[validar]** de novo antes de gravar.
