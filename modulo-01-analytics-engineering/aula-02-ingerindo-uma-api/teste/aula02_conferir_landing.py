# Databricks notebook source
# MAGIC %md
# MAGIC # Teste da aula 2 · A landing está completa?
# MAGIC
# MAGIC **O que esta etapa faz:** para cada tabela, acha a carga mais recente **que tem manifesto** e confere:
# MAGIC
# MAGIC | Teste | Pergunta | Se falhar, provável causa |
# MAGIC |---|---|---|
# MAGIC | total | linhas nos arquivos = `num_rows_total` da API = número do contrato? | paginação parou antes, ou a fonte mudou |
# MAGIC | unicidade | cada `row_idx` aparece uma vez só? | página gravada duas vezes |
# MAGIC | colunas | as colunas do contrato estão lá? | a fonte mudou o formato |
# MAGIC
# MAGIC Também lista as cargas **sem manifesto** (incompletas). Elas não entram na conferência, e a aula 3 vai ignorá-las.
# MAGIC
# MAGIC **Por quê:** "o notebook rodou sem erro" não prova que o dado veio inteiro. Este teste prova.
# MAGIC Funciona para cargas da API e do plano B.

# COMMAND ----------

import json
from pyspark.sql import functions as F

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
LANDING = f"/Volumes/{CAT}/raw/landing"

ESPERADO = {"clientes": 500, "produtos": 60, "pedidos": 1500, "eventos_pedido": 5416}
COLUNAS = {
    "clientes": {"customer_id", "nome", "email", "telefone", "cidade", "uf", "cadastrado_em"},
    "produtos": {"product_id", "nome", "categoria", "preco"},
    "pedidos": {"order_id", "customer_id", "criado_em", "itens", "valor_bruto", "valor_liquido"},
    "eventos_pedido": {"event_id", "order_id", "status", "event_ts", "canal"},
}

def tem_manifesto(pasta):
    return any(a.name == "_manifesto.json" for a in dbutils.fs.ls(pasta))

resultados, falhas = [], []
for tabela, n in ESPERADO.items():
    cargas = sorted(a.path.rstrip("/") for a in dbutils.fs.ls(f"{LANDING}/{tabela}") if a.name.startswith("carga_"))
    completas = [c for c in cargas if tem_manifesto(c)]
    for c in set(cargas) - set(completas):
        print(f"Aviso: {c.split('/landing/')[1]} sem manifesto (carga incompleta, ignorada)")
    if not completas:
        falhas.append(f"{tabela}: nenhuma carga completa")
        continue
    # A mais recente é decidida pela data do manifesto (não pelo nome da pasta: "carga_planob_..." ordenaria errado)
    manifestos = {c.replace("dbfs:", ""): json.load(open(f"{c.replace('dbfs:', '')}/_manifesto.json")) for c in completas}
    pasta, manifesto = max(manifestos.items(), key=lambda kv: kv[1]["inicio_utc"])
    df = spark.read.json(f"{pasta}/pagina_*.json").select(F.explode("rows").alias("r"))
    linhas = df.count()
    distintos = df.select("r.row_idx").distinct().count()
    colunas = set(df.select("r.row.*").columns)

    checks = {
        "total": linhas == manifesto["num_rows_total"] == n,
        "unicidade": distintos == linhas,
        "colunas": COLUNAS[tabela] <= colunas,
    }
    for nome, ok in checks.items():
        resultados.append((tabela, manifesto["carga_id"], manifesto["fonte"], nome, "OK" if ok else "FALHOU"))
        if not ok:
            falhas.append(f"{tabela}.{nome}")

display(spark.createDataFrame(resultados, "tabela string, carga_id string, fonte string, teste string, resultado string"))
assert not falhas, f"Testes que falharam: {falhas}"
print("Landing completa: todos os testes OK")
