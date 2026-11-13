# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Validar o ambiente (só para a instrutora, antes de gravar)
# MAGIC
# MAGIC Roda em ~5 minutos e responde aos itens **[validar]** do mapa da trilha. Anote o resultado de cada célula
# MAGIC em `trilha/modulo-01-do-dado-a-confianca/README.md` → seção "Free Edition".
# MAGIC
# MAGIC Usa um catálogo de teste. Ao final há uma célula de limpeza: **rode só se quiser apagar o teste.**

# COMMAND ----------

dbutils.widgets.text("catalogo", "jornada_teste")
CAT = dbutils.widgets.get("catalogo")
spark.sql(f"CREATE CATALOG IF NOT EXISTS {CAT}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CAT}.validacao")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CAT}.validacao.landing")
print("1 · Catálogo, schema e volume: OK")

# COMMAND ----------

# 2 · Quais domínios o Databricks consegue acessar?
# A Free Edition só libera internet para uma lista de domínios "confiáveis" (não publicada).
# A verificação com LinkedIn NÃO libera internet (só AI Runtime). Ver docs/decisao_api.md.
import requests

DOMINIOS = {
    # APIs de loja/e-commerce de demonstração
    "dummyjson": "https://dummyjson.com/carts?limit=5&skip=0",
    "fakestoreapi": "https://fakestoreapi.com/products?limit=1",
    "platzi_fakestore": "https://api.escuelajs.co/api/v1/products?offset=0&limit=1",
    "jsonplaceholder": "https://jsonplaceholder.typicode.com/posts/1",
    # APIs públicas brasileiras
    "brasilapi": "https://brasilapi.com.br/api/ibge/uf/v1",
    "ibge": "https://servicodados.ibge.gov.br/api/v1/localidades/regioes",
    "bcb_ptax": "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/Moedas?$format=json",
    "awesomeapi": "https://economia.awesomeapi.com.br/json/last/USD-BRL",
    # Dados abertos / ML
    "huggingface_datasets": "https://datasets-server.huggingface.co/is-valid?dataset=stanfordnlp/imdb",
    # Já sabidamente liberados
    "github_api": "https://api.github.com/rate_limit",
    "github_raw": "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore",
    "pypi": "https://pypi.org/pypi/requests/json",
}
for nome, url in DOMINIOS.items():
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "jornada-validacao/1.0"})
        print(f"2 · {nome}: OK (HTTP {resp.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"2 · {nome}: BLOQUEADO → {type(e).__name__}")

# COMMAND ----------

# 3 · A API do dataset da loja (Hugging Face) responde? Grava uma página no Volume.
# Preencha o widget "dataset_hf" com <seu-usuario>/loja-ficticia-jornada depois de publicar
# (passo a passo em docs/publicar_no_hugging_face.md).
# Célula independente: lê o catálogo do widget (funciona mesmo se a célula 1 não rodou nesta sessão).
import json, time, os, requests
from datetime import datetime, timezone
dbutils.widgets.text("catalogo", "jornada_teste")
CAT = dbutils.widgets.get("catalogo")
dbutils.widgets.text("dataset_hf", "trilhajornadadatabricks/loja-ficticia-jornada")

def get_com_retry(url, params, tentativas=5, espera=2):
    """Repete a chamada em erro temporário (429 e 5xx), esperando 2s, 4s, 8s... entre tentativas."""
    for i in range(1, tentativas + 1):
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code not in (429, 500, 502, 503, 504) or i == tentativas:
            return resp
        print(f"   {params.get('config')}: HTTP {resp.status_code}, tentativa {i}/{tentativas}; nova tentativa em {espera}s")
        time.sleep(espera)
        espera *= 2

DATASET = dbutils.widgets.get("dataset_hf")
API = "https://datasets-server.huggingface.co/rows"
ESPERADO = {"clientes": 500, "produtos": 60, "pedidos": 1500, "eventos_pedido": 5416}

if not DATASET:
    print("3 · Widget dataset_hf vazio: publique o dataset e preencha o widget.")
else:
    # Cada execução grava numa pasta nova: nunca sobrescreve arquivo na landing.
    # (Sobrescrever e ler em seguida dá InconsistentReadException no Spark.)
    PASTA = f"/Volumes/{CAT}/validacao/landing/execucao_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
    os.makedirs(PASTA, exist_ok=True)
    for config, n in ESPERADO.items():
        resp = get_com_retry(API, params={"dataset": DATASET, "config": config, "split": "train", "offset": 0, "length": 100})
        if resp.status_code != 200:
            print(f"3 · {config}: HTTP {resp.status_code} → {resp.text[:150]}")
            continue
        corpo = resp.json()
        total = corpo["num_rows_total"]
        print(f"3 · {config}: {total} linhas {'OK' if total == n else f'(esperado {n})'} | página com {len(corpo['rows'])} linhas")
        caminho = f"{PASTA}/{config}_pagina_000.json"
        with open(caminho, "w") as f:
            json.dump(corpo, f, ensure_ascii=False)
    n_lidas = spark.read.json(f"{PASTA}/pedidos_pagina_000.json").selectExpr("explode(rows) AS r").count()
    print(f"3 · Escrita no Volume + leitura pelo Spark: OK ({n_lidas} linhas de pedidos em {PASTA})")

# COMMAND ----------

# 4 · Constraints Delta (NOT NULL e CHECK)
spark.sql(f"CREATE OR REPLACE TABLE {CAT}.validacao.t (id INT NOT NULL, valor DOUBLE)")
spark.sql(f"ALTER TABLE {CAT}.validacao.t ADD CONSTRAINT valor_positivo CHECK (valor >= 0)")
try:
    spark.sql(f"INSERT INTO {CAT}.validacao.t VALUES (1, -5)")
    print("4 · ATENÇÃO: o CHECK não bloqueou o valor negativo")
except Exception as e:
    print("4 · CHECK bloqueou como esperado:", str(e)[:120])

# COMMAND ----------

# 5 · Filtro de linha (row filter) e máscara de coluna (column mask)
spark.sql(f"""
CREATE OR REPLACE TABLE {CAT}.validacao.clientes AS
SELECT * FROM VALUES (1,'South','a@x.com'), (2,'West','b@x.com') AS t(id, regiao, email)
""")
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CAT}.validacao.so_south(regiao STRING)
RETURN regiao = 'South'
""")
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CAT}.validacao.mascara_email(email STRING)
RETURN CONCAT('***@', SPLIT(email, '@')[1])
""")
try:
    spark.sql(f"ALTER TABLE {CAT}.validacao.clientes SET ROW FILTER {CAT}.validacao.so_south ON (regiao)")
    spark.sql(f"ALTER TABLE {CAT}.validacao.clientes ALTER COLUMN email SET MASK {CAT}.validacao.mascara_email")
    display(spark.table(f"{CAT}.validacao.clientes"))
    print("5 · Esperado: só a linha South, com e-mail mascarado")
except Exception as e:
    print("5 · Filtro/máscara NÃO suportado aqui:", str(e)[:300])

# COMMAND ----------

# 6 · Tags e comentários
spark.sql(f"COMMENT ON TABLE {CAT}.validacao.clientes IS 'Teste de documentação'")
try:
    spark.sql(f"ALTER TABLE {CAT}.validacao.clientes ALTER COLUMN email SET TAGS ('pii' = 'email')")
    print("6 · Tags em coluna: OK")
except Exception as e:
    print("6 · Tags em coluna falharam:", str(e)[:200])

# COMMAND ----------

# 7 · Quem sou eu e de quais grupos faço parte (base da tabela de mapeamento usuário → região)
display(spark.sql("SELECT current_user() AS usuario, is_account_group_member('admins') AS admin_conta"))

# COMMAND ----------

# 8 · Para dezembro: system tables e predictive optimization
for tabela in ["system.billing.usage", "system.query.history", "system.lakeflow.job_run_timeline"]:
    try:
        n = spark.sql(f"SELECT COUNT(*) AS n FROM {tabela}").first()["n"]
        print(f"8 · {tabela}: acessível, {n} linhas")
    except Exception as e:
        print(f"8 · {tabela}: SEM ACESSO →", str(e)[:150])
try:
    display(spark.sql(f"DESCRIBE SCHEMA EXTENDED {CAT}.validacao"))
    print("8 · Procure 'Predictive Optimization' na saída acima")
except Exception as e:
    print(str(e)[:200])

# COMMAND ----------

# MAGIC %md
# MAGIC ### Limpeza (opcional; apaga tudo que este notebook criou)
# MAGIC Descomente e rode só se quiser remover o catálogo de teste.

# COMMAND ----------

# spark.sql(f"DROP CATALOG IF EXISTS {CAT} CASCADE")
