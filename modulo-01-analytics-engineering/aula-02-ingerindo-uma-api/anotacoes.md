# Aula 2 · Anotações

> Minhas notas sobre o notebook da aula, passo a passo. Use junto com o notebook aberto: cada seção aqui tem o mesmo nome do passo lá.
> Os blocos de código têm um botão de copiar no canto direito (passe o mouse em cima).

## Em uma frase

Buscar os dados da loja numa API, página por página, e guardar as respostas **exatamente como vieram** num Volume, com um recibo (o manifesto) que prova que veio tudo.

```
                  ┌───────────── Databricks (serverless) ─────────────┐
API Hugging Face  │  notebook aula02                                   │
/rows?offset=…    │   1. pede 100 linhas  ──► 2. confere  ──► 3. grava │──► /Volumes/<catalogo>/raw/landing/
   ▲              │        ▲   │ erro temporário? espera e repete      │      pedidos/carga_AAAAMMDD_HHMMSS/
   └──────────────┼────────┘   ▼ erro nosso? para com mensagem         │        pagina_0000.json … 0014.json
                  └────────────────────────────────────────────────────┘        _manifesto.json
```

---

## Passo 0 · Parâmetros (widgets)

O **widget** é a caixinha que aparece no topo do notebook. Uma linha cria a caixa, a outra lê o que está escrito nela:

```python
dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
```

Por que não escrever o nome do catálogo direto no código? Porque assim o mesmo notebook roda em qualquer catálogo (um de teste, um seu) sem editar nada. Regra do lab: **nada de nome fixo no código**.

`COLUNAS_ESPERADAS` é a seção 3 do [contrato de dados](../docs/contrato_de_dados.md) virando código: as colunas que a gente combinou receber.

Você deve ver algo assim:
```
Catálogo: jornada_comercial | Dataset: trilhajornadadatabricks/loja-ficticia-jornada | Landing: /Volumes/jornada_comercial/raw/landing
```

## Passo 1 · A rede deixa?

A Free Edition só acessa uma lista de sites liberados ([limites da Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)). Em empresa é igual: o firewall decide.

```
IBGE: SEM ACESSO → ConnectTimeout
Hugging Face (nossa fonte): HTTP 200
```

- `ConnectTimeout`: o pedido nem chegou no servidor. Não é bug no código, é a rede.
- `HTTP 200`: chegou e respondeu.

A lista de sites muda sem aviso, então pode ser que no seu teste o resultado seja outro. O que importa é o hábito: **antes de culpar o código, teste a rede**.

## Passo 2 · A primeira chamada

- **API REST:** um endereço na internet que devolve dados (aqui em JSON) quando você faz um pedido `GET`.
- **Endpoint:** o caminho específico. Aqui é `/rows`.
- **Parâmetros:** o que vem depois do `?` na URL. O `requests` monta isso a partir do dicionário `params`.

Quer ver a resposta crua? Cole esta URL no navegador:

```
https://datasets-server.huggingface.co/rows?dataset=trilhajornadadatabricks/loja-ficticia-jornada&config=pedidos&split=train&offset=0&length=3
```

No notebook, a saída fica assim:
```
Status: 200
Chaves da resposta: ['features', 'rows', 'num_rows_total', 'num_rows_per_page', 'partial']
Total de linhas na fonte (num_rows_total): 1500
Colunas (features): ['order_id', 'customer_id', 'criado_em', 'itens', 'valor_bruto', 'valor_liquido']
```

Três chaves importam para a gente: `rows` (os dados), `num_rows_total` (quantas linhas existem) e `features` (as colunas). Cada item de `rows` vem embrulhado assim: `{"row_idx": posição, "row": {o dado}, "truncated_cells": []}`.

Se a URL do notebook aparecer com `%2F`, é só a `/` codificada. O `requests` faz isso sozinho.

## Erro de propósito 2 · Pedir tudo de uma vez

```
Status: 422 → {"error":"Parameter 'length' must not be greater than 100"}
```

Código **4xx** quer dizer "o problema está no seu pedido". Tentar de novo não adianta, tem que mudar o pedido. E repare que a própria API conta o limite: 100.

## Erro de propósito 3 · Esquecer de paginar

```
Status 200 | vieram 100 de 1500 pedidos
```

Esse é o erro mais perigoso: o que **não dá erro**. HTTP 200 diz que a chamada funcionou, não que veio tudo. Por isso a gente guarda o `num_rows_total` e confere no fim.

## Passo 3 · Tentar de novo (retry)

- **Retry:** repetir a chamada quando a falha é passageira.
- **Backoff exponencial:** a espera dobra a cada tentativa (2 s, 4 s, 8 s…), para não ficar martelando um serviço que já está com problema.
- **Rate limit (429):** a API limita quantas chamadas cada um faz por minuto. A carga inteira são 76 chamadas, então é normal aparecer um 429 no meio. O notebook espera 60 s e segue.

| Código | Quem errou | Tentar de novo? |
|---|---|---|
| 200 | ninguém | — |
| 400, 404, 422 | nós (pedido errado) | não: corrigir o pedido |
| 429 | ninguém: chamadas demais | sim, depois de esperar |
| 500, 502, 503, 504 | o servidor | sim, depois de esperar |
| timeout / conexão caiu | a rede | sim, depois de esperar |

A [doc do Hugging Face](https://huggingface.co/docs/hub/en/rate-limits) fala de um cabeçalho `RateLimit` com o tempo até liberar. Se ele vier na resposta, o código usa; se não vier, espera 60 s.

Faça o teste: peça `config: "pedido"` (sem o "s"). O 404 para na hora, sem tentar de novo:
```
Erro definitivo HTTP 404 ... {"error":"Not found."}
```

## Passo 4 · Conferir as colunas (schema)

**Schema** é a lista de colunas (e tipos) que a gente espera.

- Coluna **faltando** → para tudo (`ValueError`). Sem ela, a aula 3 quebraria ou, pior, calcularia errado sem avisar.
- Coluna **nova** → só avisa. Não quebra nada.

Quer ver acontecer? Troque o nome de uma coluna em `COLUNAS_ESPERADAS` e rode a carga de `pedidos`:

```python
"valor_liq",   # era "valor_liquido"
```

Depois volte para `"valor_liquido"`.

## Passo 5 · O laço de paginação (`baixar_tabela`)

**Paginação por offset:** `offset=0, length=100` traz as linhas 0 a 99; `offset=100` traz de 100 a 199; e assim vai até `offset >= num_rows_total`.

O esqueleto do laço:

```python
offset = 0
while True:
    # pede 100 linhas a partir do offset
    # na 1ª página: guarda num_rows_total e confere as colunas
    # grava a resposta crua num arquivo pagina_NNNN.json
    offset += 100
    if offset >= total:
        break
```

Três escolhas que fiz no código, e por quê:

| Escolha | Por quê |
|---|---|
| Gravar `r.text` (a resposta crua), não um JSON "arrumado" | É a prova do que a fonte mandou. Se a aula 3 tiver bug, dá para refazer sem chamar a API de novo |
| Uma pasta nova por carga (`carga_AAAAMMDD_HHMMSS`, hora UTC) | Nunca sobrescreve nada. E dá para saber exatamente o que veio em cada dia |
| `_manifesto.json` só no fim, se o total bateu | Pasta **sem** manifesto = carga incompleta. Quem lê a landing (o teste e a aula 3) ignora essas pastas |

**UTC** é o horário universal (Brasília = UTC−3). Uso UTC para o nome da pasta não depender do fuso de quem roda.

## Passo 6 · Rodar as 4 tabelas

Todas usam o mesmo `CARGA_ID`, para ficar claro que foram buscadas juntas. A saída fica parecida com esta:

```
clientes: 500 linhas em 5 páginas
produtos: 60 linhas em 1 páginas
   HTTP 502 na tentativa 1/6; nova tentativa em 2s
pedidos: 1500 linhas em 15 páginas
   HTTP 429 (RateLimit: não informado) na tentativa 1/6; nova tentativa em 60s
eventos_pedido: 5416 linhas em 55 páginas
```

Apareceu 429 ou 502? Ótimo: é o retry fazendo o trabalho dele. A carga toda leva de 2 a 6 minutos.

## Passo 7 · Checkpoint com Spark

- `spark.read.json(".../pagina_*.json")` lê todas as páginas de uma vez (uma linha por página).
- `F.explode("rows")` abre a lista `rows`: cada registro vira uma linha.
- Contar `row_idx` distintos = contar linhas sem repetição. Se bater com o total, nenhuma página veio duplicada.

Esperado: `clientes 500 · produtos 60 · pedidos 1500 · eventos_pedido 5416`, todos `OK`.

Para ver os arquivos: **Catalog → jornada_comercial → raw → landing**.

---

## O teste (`teste/aula02_conferir_landing`)

Para cada tabela, ele pega a carga completa mais recente (a que tem manifesto) e confere o total, se algum `row_idx` se repete e as colunas. Cargas sem manifesto aparecem só como aviso. No fim tem `assert`: se algo falhar, o notebook fica vermelho.

```
Aviso: eventos_pedido/carga_..._... sem manifesto (carga incompleta, ignorada)
...
Landing completa: todos os testes OK
```

## Plano B (`setup/02_plano_b_sem_api`)

Se a API estiver bloqueada ou fora do ar, esse notebook lê os `.jsonl` de `setup/plano_b/` (os mesmos arquivos publicados no Hugging Face) e grava no Volume **no mesmo formato da API**, com manifesto `"fonte": "plano_b"`. Para o resto do curso, tanto faz de onde veio.

## Glossário

| Termo | Em uma frase |
|---|---|
| Volume | Pasta de arquivos governada pelo Unity Catalog (`/Volumes/catalogo/schema/volume/`) |
| Landing | Onde os arquivos chegam como vieram, antes de qualquer tratamento |
| Manifesto | O recibo da carga: quantas páginas e linhas, quando, de onde |
| Idempotente | Rodar de novo não estraga nada (aqui: cada carga cria uma pasta nova) |
| Serverless | Computação que o Databricks liga e desliga para você; a opção da Free Edition |
