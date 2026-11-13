# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 2 · Ingerindo uma API de verdade
# MAGIC
# MAGIC **O que esta etapa faz:** busca as 4 tabelas da loja (`clientes`, `produtos`, `pedidos`, `eventos_pedido`) numa API REST
# MAGIC pública e grava as respostas **do jeito que vieram** no Volume `raw.landing`, uma pasta por carga, com um manifesto.
# MAGIC
# MAGIC **Por quê:** a aula 3 só pode confiar no dado se a gente souber de onde ele veio, quando, e se veio inteiro.
# MAGIC Por isso aqui não transformamos nada: só buscamos, conferimos e guardamos.
# MAGIC
# MAGIC ```
# MAGIC API (Hugging Face) ──requests──▶ /Volumes/<catalogo>/raw/landing/<tabela>/carga_<AAAAMMDD_HHMMSS>/
# MAGIC                                     ├── pagina_0000.json   ← resposta crua da API
# MAGIC                                     ├── pagina_0001.json
# MAGIC                                     └── _manifesto.json    ← "recibo" da carga: quantas páginas, linhas, quando
# MAGIC ```
# MAGIC
# MAGIC Antes: rode `setup/01_criar_ambiente` (na pasta `setup/` do módulo) com o mesmo catálogo.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 0 · Parâmetros
# MAGIC Widgets são as caixinhas no topo do notebook: mudam o valor sem mexer no código.

# COMMAND ----------

import json, os, time
from datetime import datetime, timezone
import requests

dbutils.widgets.text("catalogo", "jornada_comercial")
dbutils.widgets.text("dataset_hf", "trilhajornadadatabricks/loja-ficticia-jornada")
CAT = dbutils.widgets.get("catalogo")
DATASET = dbutils.widgets.get("dataset_hf")

API = "https://datasets-server.huggingface.co/rows"
LANDING = f"/Volumes/{CAT}/raw/landing"
TAMANHO_PAGINA = 100  # o máximo que a API aceita (ver erro proposital 2)
CABECALHOS = {"User-Agent": "jornada-dados-lab/1.0"}  # identifica quem está chamando; boa educação com API pública

# O "contrato" da fonte: colunas que esperamos em cada tabela (docs/contrato_de_dados.md, seção 3)
COLUNAS_ESPERADAS = {
    "clientes": ["customer_id", "nome", "email", "telefone", "cidade", "uf", "cadastrado_em"],
    "produtos": ["product_id", "nome", "categoria", "preco"],
    "pedidos": ["order_id", "customer_id", "criado_em", "itens", "valor_bruto", "valor_liquido"],
    "eventos_pedido": ["event_id", "order_id", "status", "event_ts", "canal"],
}
print(f"Catálogo: {CAT} | Dataset: {DATASET} | Landing: {LANDING}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 1 · A rede deixa? (erro proposital 1)
# MAGIC
# MAGIC Na Free Edition o Databricks só acessa uma lista de sites liberados, que **não é publicada e muda sem aviso**.
# MAGIC Em empresa é igual: firewall. Antes de culpar o código, teste a rede.
# MAGIC
# MAGIC - `HTTP 200` → a rede chegou e o serviço respondeu.
# MAGIC - `ConnectTimeout` / `ConnectionError` → a rede **não** chegou (domínio bloqueado). Não adianta mexer no código.

# COMMAND ----------

for nome, url in {
    "IBGE (bloqueado em 09 e 10/11)": "https://servicodados.ibge.gov.br/api/v1/localidades/regioes",
    "Hugging Face (nossa fonte)": "https://datasets-server.huggingface.co/is-valid?dataset=" + DATASET,
}.items():
    try:
        r = requests.get(url, timeout=10, headers=CABECALHOS)
        print(f"{nome}: HTTP {r.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"{nome}: SEM ACESSO → {type(e).__name__}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 2 · A primeira chamada: o que a API devolve?
# MAGIC
# MAGIC Uma chamada = uma URL com parâmetros (o que vem depois do `?`):
# MAGIC
# MAGIC | Parâmetro | Significado |
# MAGIC |---|---|
# MAGIC | `dataset` | qual dataset (usuário/nome) |
# MAGIC | `config` | qual tabela |
# MAGIC | `split` | partição do dataset; aqui sempre `train` |
# MAGIC | `offset` | a partir de qual linha (começa em 0) |
# MAGIC | `length` | quantas linhas trazer (máximo 100) |

# COMMAND ----------

r = requests.get(API, params={"dataset": DATASET, "config": "pedidos", "split": "train", "offset": 0, "length": 3},
                 headers=CABECALHOS, timeout=30)
print("URL chamada:", r.url)
print("Status:", r.status_code)
corpo = r.json()
print("Chaves da resposta:", list(corpo))
print("Total de linhas na fonte (num_rows_total):", corpo["num_rows_total"])
print("Colunas (features):", [f["name"] for f in corpo["features"]])
print("Primeira linha:", json.dumps(corpo["rows"][0], ensure_ascii=False)[:400])

# COMMAND ----------

# MAGIC %md
# MAGIC Cada item de `rows` tem `row_idx` (posição da linha na fonte) e `row` (o dado em si).
# MAGIC `num_rows_total` diz quantas linhas existem: é com ele que sabemos quando parar e se veio tudo.
# MAGIC
# MAGIC ## Erro proposital 2 · "Me dá tudo de uma vez"

# COMMAND ----------

r = requests.get(API, params={"dataset": DATASET, "config": "pedidos", "split": "train", "offset": 0, "length": 1000},
                 headers=CABECALHOS, timeout=30)
print("Status:", r.status_code, "→", r.text)
# Esperado: HTTP 422 → {"error":"Parameter 'length' must not be greater than 100"}
# 4xx = o problema é o pedido (nosso). Não adianta tentar de novo: tem que corrigir o pedido.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Erro proposital 3 · Esquecer de paginar
# MAGIC Uma chamada só, com o máximo permitido. Parece que deu certo (HTTP 200)... mas veio tudo?

# COMMAND ----------

r = requests.get(API, params={"dataset": DATASET, "config": "pedidos", "split": "train", "offset": 0, "length": 100},
                 headers=CABECALHOS, timeout=30)
corpo = r.json()
print(f"Status {r.status_code} | vieram {len(corpo['rows'])} de {corpo['num_rows_total']} pedidos")
# 100 de 1500: HTTP 200 não quer dizer "veio tudo". Sempre compare com o total.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 3 · Tentar de novo quando a falha é temporária (retry)
# MAGIC
# MAGIC Em 10/11, durante a preparação desta aula, a API devolveu `502 Bad Gateway` e `503` por alguns minutos.
# MAGIC Não era erro nosso: o serviço deles caiu. A regra:
# MAGIC
# MAGIC | Resposta | O que significa | O que fazer |
# MAGIC |---|---|---|
# MAGIC | 200 | deu certo | seguir |
# MAGIC | 429 | "calma, muitas chamadas" | esperar e tentar de novo |
# MAGIC | 500, 502, 503, 504 | o servidor falhou | esperar e tentar de novo |
# MAGIC | sem resposta (timeout, conexão caiu) | a rede oscilou | esperar e tentar de novo |
# MAGIC | outros 4xx (400, 404, 422…) | nosso pedido está errado | **parar** e corrigir |
# MAGIC
# MAGIC A espera dobra a cada tentativa (2s, 4s, 8s, 16s, 32s): isso se chama *backoff exponencial*.
# MAGIC Dá tempo para o serviço voltar sem bombardear ele de chamadas.
# MAGIC
# MAGIC **O caso do 429 (limite de chamadas):** API gratuita limita quantas chamadas cada IP faz por minuto.
# MAGIC Medido em 10/11 (não documentado, pode mudar): depois de ~40 a 55 chamadas em sequência, o `/rows` responde 429
# MAGIC e libera de novo em ~60 s. A carga inteira são 76 chamadas, então **vamos bater nesse limite**: por isso
# MAGIC esperamos 1 s entre páginas e, no 429, esperamos 60 s. Se a API mandar o cabeçalho `RateLimit`
# MAGIC (`t=` = segundos até liberar, [doc do Hub](https://huggingface.co/docs/hub/en/rate-limits)), usamos esse tempo.
# MAGIC Na Free Edition o IP de saída é compartilhado com outros usuários, então a cota pode acabar ainda mais cedo.

# COMMAND ----------

import re

STATUS_TEMPORARIOS = {429, 500, 502, 503, 504}
ESPERA_429 = 60  # segundos; medido em 10/11

def segundos_ate_renovar(r):
    """Lê o cabeçalho RateLimit (ex.: '"api";r=0;t=87') e devolve o t, em segundos. None se não vier."""
    m = re.search(r"t=(\d+)", r.headers.get("RateLimit", ""))
    return int(m.group(1)) + 1 if m else None

def get_com_retry(params, tentativas=6, espera=2):
    """Chama a API. Em falha temporária, espera e tenta de novo. Em erro definitivo, para com mensagem clara."""
    for tentativa in range(1, tentativas + 1):
        aguardar = min(espera, 60)
        try:
            r = requests.get(API, params=params, headers=CABECALHOS, timeout=30)
            if r.status_code == 200:
                return r
            if r.status_code not in STATUS_TEMPORARIOS:
                raise RuntimeError(f"Erro definitivo HTTP {r.status_code} em {params}: {r.text[:200]}")
            motivo = f"HTTP {r.status_code}"
            if r.status_code == 429:
                motivo += f" (RateLimit: {r.headers.get('RateLimit', 'não informado')})"
                aguardar = segundos_ate_renovar(r) or ESPERA_429
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            motivo = type(e).__name__
        if tentativa == tentativas:
            raise RuntimeError(f"Desisti após {tentativas} tentativas ({motivo}) em {params}")
        print(f"   {motivo} na tentativa {tentativa}/{tentativas}; nova tentativa em {aguardar}s")
        time.sleep(aguardar)
        espera *= 2

# Teste rápido: um config que não existe → 404 → para na hora, sem tentar de novo.
try:
    get_com_retry({"dataset": DATASET, "config": "pedido", "split": "train", "offset": 0, "length": 1})
except RuntimeError as e:
    print(e)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 4 · Conferir o formato (validação de schema)
# MAGIC
# MAGIC Se a fonte trocar o nome de uma coluna, queremos descobrir **aqui**, na entrada, e não num relatório errado semanas depois.
# MAGIC A API manda a lista de colunas em `features`. Comparamos com o que o contrato espera.

# COMMAND ----------

def validar_colunas(tabela, features):
    recebidas = [f["name"] for f in features]
    esperadas = COLUNAS_ESPERADAS[tabela]
    faltando = [c for c in esperadas if c not in recebidas]
    novas = [c for c in recebidas if c not in esperadas]
    if faltando:
        raise ValueError(f"{tabela}: a fonte mudou! Faltando: {faltando}. Novas: {novas}")
    if novas:
        print(f"   Aviso {tabela}: colunas novas na fonte (não quebram a carga): {novas}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 5 · Baixar uma tabela inteira, página por página
# MAGIC
# MAGIC O loop: começa no `offset` 0, pede 100, grava, soma 100 no `offset`, repete até chegar no `num_rows_total`.
# MAGIC
# MAGIC Três decisões importantes:
# MAGIC 1. **Gravar a resposta crua** (`r.text`), sem mexer: é a prova do que a fonte mandou.
# MAGIC 2. **Uma pasta nova por carga** (`carga_AAAAMMDD_HHMMSS`): nunca sobrescrevemos. Dá para refazer ou auditar qualquer dia.
# MAGIC 3. **Manifesto no fim**: só escrevemos o `_manifesto.json` se a carga terminou e bateu o total.
# MAGIC    Pasta sem manifesto = carga incompleta, e a aula 3 vai ignorar.

# COMMAND ----------

def baixar_tabela(tabela, carga_id):
    pasta = f"{LANDING}/{tabela}/carga_{carga_id}"
    os.makedirs(pasta, exist_ok=True)
    inicio = datetime.now(timezone.utc)
    offset, pagina, linhas, total = 0, 0, 0, None

    while total is None or offset < total:
        params = {"dataset": DATASET, "config": tabela, "split": "train", "offset": offset, "length": TAMANHO_PAGINA}
        r = get_com_retry(params)
        corpo = r.json()
        if total is None:                      # primeira página: descobre o total e confere o formato
            total = corpo["num_rows_total"]
            validar_colunas(tabela, corpo["features"])
        with open(f"{pasta}/pagina_{pagina:04d}.json", "w") as f:
            f.write(r.text)                    # resposta crua, exatamente como veio
        linhas += len(corpo["rows"])
        offset += TAMANHO_PAGINA
        pagina += 1
        time.sleep(1)                          # pausa entre páginas: respeitar o limite da API gratuita

    if linhas != total:
        raise RuntimeError(f"{tabela}: vieram {linhas} linhas, a fonte diz {total}. Carga incompleta, sem manifesto.")

    manifesto = {
        "tabela": tabela, "carga_id": carga_id, "fonte": API, "dataset": DATASET,
        "paginas": pagina, "linhas": linhas, "num_rows_total": total,
        "inicio_utc": inicio.isoformat(), "fim_utc": datetime.now(timezone.utc).isoformat(), "status": "completa",
    }
    with open(f"{pasta}/_manifesto.json", "w") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)
    return manifesto

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 6 · Rodar a carga das 4 tabelas
# MAGIC Todas usam o mesmo `carga_id`: assim sabemos que foram buscadas juntas.

# COMMAND ----------

CARGA_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
manifestos = []
for tabela in COLUNAS_ESPERADAS:
    m = baixar_tabela(tabela, CARGA_ID)
    print(f"{tabela}: {m['linhas']} linhas em {m['paginas']} páginas")
    manifestos.append(m)
display(spark.createDataFrame(manifestos).select("tabela", "carga_id", "paginas", "linhas", "num_rows_total", "status"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 7 · Checkpoint: o Spark enxerga o que gravamos?
# MAGIC
# MAGIC Lemos os arquivos de volta com o Spark (que é como a aula 3 vai ler) e contamos as linhas.
# MAGIC `explode(rows)` transforma a lista `rows` de cada página em uma linha por registro.
# MAGIC Contamos também `row_idx` distintos: se uma página tivesse vindo repetida, o número seria diferente.

# COMMAND ----------

from pyspark.sql import functions as F

ESPERADO = {"clientes": 500, "produtos": 60, "pedidos": 1500, "eventos_pedido": 5416}
resultado = []
for tabela, n in ESPERADO.items():
    df = (spark.read.json(f"{LANDING}/{tabela}/carga_{CARGA_ID}/pagina_*.json")
          .select(F.explode("rows").alias("r")))
    linhas = df.count()
    distintos = df.select("r.row_idx").distinct().count()
    resultado.append((tabela, n, linhas, distintos, "OK" if linhas == distintos == n else "CONFERIR"))
display(spark.createDataFrame(resultado, "tabela string, esperado int, linhas int, row_idx_distintos int, resultado string"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## O que ficou no Volume
# MAGIC Abra também pela interface: **Catalog → `<catalogo>` → raw → landing**.

# COMMAND ----------

for tabela in ESPERADO:
    arquivos = dbutils.fs.ls(f"{LANDING}/{tabela}/carga_{CARGA_ID}")
    print(f"{tabela}/carga_{CARGA_ID}/: {len(arquivos)} arquivos →", ", ".join(a.name for a in arquivos[:3]), "…", arquivos[-1].name)
print("\nManifesto de pedidos:")
print(open(f"{LANDING}/pedidos/carga_{CARGA_ID}/_manifesto.json").read())
