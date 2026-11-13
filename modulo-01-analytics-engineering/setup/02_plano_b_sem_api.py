# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Plano B: carregar a landing sem a API
# MAGIC
# MAGIC **Quando usar:** só se a API do Hugging Face estiver bloqueada ou fora do ar e você não puder esperar.
# MAGIC
# MAGIC **O que esta etapa faz:** lê os mesmos dados que estão publicados na API (arquivos `.jsonl` em `setup/plano_b/`,
# MAGIC que vieram junto com o repositório) e grava no Volume **no mesmo formato da resposta da API**: páginas de 100
# MAGIC linhas + `_manifesto.json`. Assim a aula 3 funciona igual, venha o dado da API ou daqui.
# MAGIC
# MAGIC **Por quê:** todo pipeline que depende de fonte externa precisa de um caminho alternativo combinado.
# MAGIC O manifesto registra `"fonte": "plano_b"`, então dá para saber de onde veio cada carga.
# MAGIC
# MAGIC Antes: rode `01_criar_ambiente.py`. Este notebook precisa estar na pasta `setup/` do repositório clonado
# MAGIC (ele procura os arquivos na subpasta `plano_b/`, ao lado dele).

# COMMAND ----------

import json, os
from datetime import datetime, timezone

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
LANDING = f"/Volumes/{CAT}/raw/landing"
ORIGEM = os.path.join(os.getcwd(), "plano_b")  # no Databricks, a pasta atual é a pasta do notebook
TAMANHO_PAGINA = 100

FEATURES = json.load(open(f"{ORIGEM}/features.json"))
CARGA_ID = "planob_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

for tabela, features in FEATURES.items():
    linhas = [json.loads(l) for l in open(f"{ORIGEM}/{tabela}.jsonl")]
    pasta = f"{LANDING}/{tabela}/carga_{CARGA_ID}"
    os.makedirs(pasta, exist_ok=True)
    inicio = datetime.now(timezone.utc)
    paginas = 0
    for offset in range(0, len(linhas), TAMANHO_PAGINA):
        corpo = {
            "features": features,
            "rows": [{"row_idx": offset + i, "row": r, "truncated_cells": []}
                     for i, r in enumerate(linhas[offset:offset + TAMANHO_PAGINA])],
            "num_rows_total": len(linhas), "num_rows_per_page": TAMANHO_PAGINA, "partial": False,
        }
        with open(f"{pasta}/pagina_{paginas:04d}.json", "w") as f:
            json.dump(corpo, f, ensure_ascii=False)
        paginas += 1
    manifesto = {"tabela": tabela, "carga_id": CARGA_ID, "fonte": "plano_b", "dataset": "arquivos setup/plano_b",
                 "paginas": paginas, "linhas": len(linhas), "num_rows_total": len(linhas),
                 "inicio_utc": inicio.isoformat(), "fim_utc": datetime.now(timezone.utc).isoformat(), "status": "completa"}
    with open(f"{pasta}/_manifesto.json", "w") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=2)
    print(f"{tabela}: {len(linhas)} linhas em {paginas} páginas → {pasta}")
