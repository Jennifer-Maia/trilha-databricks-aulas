# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 3 · Exercícios: escreva as regras em SQL (gabarito)
# MAGIC
# MAGIC Este é o gabarito dos exercícios. Tente primeiro em `exercicio/aula03_exercicios`.
# MAGIC
# MAGIC Na aula, as regras do contrato viraram código. Aqui é você quem escreve cada uma, em SQL:
# MAGIC
# MAGIC | # | Exercício | Regra |
# MAGIC |---|---|---|
# MAGIC | 1 | Uma grafia por status | RN-01 |
# MAGIC | 2 | Quarentena | RN-07 |
# MAGIC | 3 | Sem duplicados (pela chave certa) | RN-02 |
# MAGIC | 4 | Status atual de cada pedido | RN-03 |
# MAGIC | 5 | Vendas por região e mês | RN-04, RN-05 e RN-06 |
# MAGIC
# MAGIC **Como funciona:** escreva o `SELECT` dentro das aspas triplas onde estiver `✏️` e rode a célula. Ela cria uma *view temporária*
# MAGIC (uma consulta com nome, que só existe nesta sessão: não mexe nas tabelas da aula). Depois rode a célula **Conferir** logo abaixo.
# MAGIC O gabarito está em `solucao/aula03_exercicios_gabarito`.
# MAGIC
# MAGIC Antes: a landing da aula 2 precisa estar completa. A preparação abaixo monta a bronze.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Preparação (só rodar)

# COMMAND ----------

import json
from pyspark.sql import functions as F

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
LANDING = f"/Volumes/{CAT}/raw/landing"
spark.sql(f"USE CATALOG {CAT}")

def ultima_carga_completa(tabela):
    cargas = [a.path.replace("dbfs:", "").rstrip("/") for a in dbutils.fs.ls(f"{LANDING}/{tabela}") if a.name.startswith("carga_")]
    completas = {}
    for pasta in cargas:
        if any(a.name == "_manifesto.json" for a in dbutils.fs.ls(pasta)):
            with open(f"{pasta}/_manifesto.json") as f:
                completas[pasta] = json.load(f)
    if not completas:
        raise RuntimeError(f"{tabela}: nenhuma carga completa na landing. Rode a aula 2 (ou o plano B) antes.")
    return max(completas.items(), key=lambda kv: kv[1]["inicio_utc"])

for tabela in ["clientes", "produtos", "pedidos", "eventos_pedido"]:
    pasta, manifesto = ultima_carga_completa(tabela)
    (spark.read.json(f"{pasta}/pagina_*.json")
     .select(F.explode("rows").alias("r"), F.col("_metadata.file_path").alias("_arquivo"))
     .select("r.row.*", F.col("r.row_idx").alias("_row_idx"), "_arquivo")
     .withColumn("_carga_id", F.lit(manifesto["carga_id"]))
     .withColumn("_ingerido_em", F.current_timestamp())
     .write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"bronze.{tabela}"))
    print(f"bronze.{tabela} pronta")

# COMMAND ----------

pendentes = set()

def criar_view(nome, sql):
    """Cria a view temporária com o seu SELECT. Se ainda estiver em branco, só avisa."""
    if not sql.strip() or "✏️" in sql:
        pendentes.add(nome)
        print(f"⏳ {nome}: escreva o SELECT e rode de novo.")
        return
    pendentes.discard(nome)
    spark.sql(f"CREATE OR REPLACE TEMP VIEW {nome} AS {sql}")
    print(f"View {nome} criada. Agora rode a célula Conferir.")

def um(sql):
    return spark.sql(sql).first()[0]

def pronta(nome):
    if nome in pendentes:
        raise NotImplementedError
    return True

def conferir(exercicio, casos):
    tudo_certo = True
    for descricao, caso in casos:
        try:
            passou, detalhe = bool(caso()), ""
        except NotImplementedError:
            print(f"⏳ {exercicio}: ainda falta escrever o SELECT.")
            return
        except Exception as e:
            passou, detalhe = False, f"  →  {type(e).__name__}: {str(e).splitlines()[0][:160]}"
        print(("✅ " if passou else "❌ ") + descricao + detalhe)
        tudo_certo = tudo_certo and passou
    print(f"\n🎉 {exercicio}: tudo certo!" if tudo_certo else f"\n{exercicio}: ainda não. Releia a dica e tente de novo.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 1 · RN-01: uma grafia por status
# MAGIC
# MAGIC Em `bronze.eventos_pedido`, o status aparece como `Entregue`, `ENTREGUE`, `delivered`, `Cancelado`, `CANCELED`…
# MAGIC Escreva um `SELECT` que devolva **todas** as linhas, com as colunas `event_id` e `status`, este já normalizado
# MAGIC para um destes cinco: `criado`, `pago`, `enviado`, `entregue`, `cancelado`.
# MAGIC
# MAGIC **Dica:** `lower(trim(status))` resolve maiúsculas e espaços. Sobram duas palavras em inglês: um `CASE` resolve.

# COMMAND ----------

sql_ex1 = """
SELECT
  event_id,
  CASE lower(trim(status))
    WHEN 'delivered' THEN 'entregue'
    WHEN 'canceled'  THEN 'cancelado'
    ELSE lower(trim(status))
  END AS status
FROM bronze.eventos_pedido
"""
criar_view("ex1_status", sql_ex1)

# COMMAND ----------

conferir("Exercício 1", [
    ("a view existe", lambda: pronta("ex1_status")),
    ("todas as 5.416 linhas continuam lá", lambda: um("SELECT COUNT(*) FROM ex1_status") == 5416),
    ("só sobraram os 5 status válidos", lambda: um("SELECT COUNT(*) FROM ex1_status WHERE status NOT IN ('criado','pago','enviado','entregue','cancelado')") == 0),
    ("'delivered' virou 'entregue' (1.101 linhas entregue)", lambda: um("SELECT COUNT(*) FROM ex1_status WHERE status = 'entregue'") == 1101),
    ("'CANCELED' virou 'cancelado' (176 linhas cancelado)", lambda: um("SELECT COUNT(*) FROM ex1_status WHERE status = 'cancelado'") == 176),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 2 · RN-07: a quarentena
# MAGIC
# MAGIC Escreva um `SELECT` com os eventos que **não** podem seguir: sem data (`event_ts` nulo) ou de pedido que não existe em `bronze.pedidos`.
# MAGIC Colunas: `event_id`, `order_id` e `motivo` (`'sem_data'` ou `'pedido_inexistente'`).
# MAGIC
# MAGIC **Dica:** para achar o pedido que não existe, faça um `LEFT JOIN` com `bronze.pedidos` e procure onde o lado dos pedidos veio nulo.

# COMMAND ----------

sql_ex2 = """
SELECT
  e.event_id,
  e.order_id,
  CASE WHEN e.event_ts IS NULL THEN 'sem_data' ELSE 'pedido_inexistente' END AS motivo
FROM bronze.eventos_pedido e
LEFT JOIN bronze.pedidos p ON p.order_id = e.order_id
WHERE e.event_ts IS NULL OR p.order_id IS NULL
"""
criar_view("ex2_quarentena", sql_ex2)

# COMMAND ----------

conferir("Exercício 2", [
    ("a view existe", lambda: pronta("ex2_quarentena")),
    ("17 eventos na quarentena", lambda: um("SELECT COUNT(*) FROM ex2_quarentena") == 17),
    ("12 com motivo 'sem_data'", lambda: um("SELECT COUNT(*) FROM ex2_quarentena WHERE motivo = 'sem_data'") == 12),
    ("5 com motivo 'pedido_inexistente'", lambda: um("SELECT COUNT(*) FROM ex2_quarentena WHERE motivo = 'pedido_inexistente'") == 5),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 3 · RN-02: sem duplicados, pela chave certa
# MAGIC
# MAGIC Junte o que você já fez: pegue os eventos **válidos** (os que não foram para a quarentena), com o status normalizado,
# MAGIC e deixe **uma linha por evento**. Colunas: `event_id`, `order_id`, `status` e `event_ts` (como `TIMESTAMP`).
# MAGIC
# MAGIC **Dica:** `QUALIFY ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...) = 1` fica com a primeira linha de cada grupo.
# MAGIC A pergunta é: qual coluna vai no `PARTITION BY`? (Lembre do erro de propósito da aula.)

# COMMAND ----------

sql_ex3 = """
SELECT
  e.event_id,
  e.order_id,
  CASE lower(trim(e.status))
    WHEN 'delivered' THEN 'entregue'
    WHEN 'canceled'  THEN 'cancelado'
    ELSE lower(trim(e.status))
  END AS status,
  CAST(e.event_ts AS TIMESTAMP) AS event_ts
FROM bronze.eventos_pedido e
JOIN bronze.pedidos p ON p.order_id = e.order_id   -- RN-07: o pedido existe
WHERE e.event_ts IS NOT NULL                        -- RN-07: tem data
QUALIFY ROW_NUMBER() OVER (PARTITION BY e.event_id ORDER BY e.event_ts) = 1
"""
criar_view("ex3_eventos", sql_ex3)

# COMMAND ----------

conferir("Exercício 3", [
    ("a view existe", lambda: pronta("ex3_eventos")),
    ("não deduplicou por pedido (isso deixaria só 1.500 linhas)", lambda: um("SELECT COUNT(*) FROM ex3_eventos") != 1500),
    ("cada event_id aparece uma vez", lambda: um("SELECT COUNT(*) - COUNT(DISTINCT event_id) FROM ex3_eventos") == 0),
    ("5.226 eventos válidos e únicos", lambda: um("SELECT COUNT(*) FROM ex3_eventos") == 5226),
    ("nenhum evento sem data", lambda: um("SELECT COUNT(*) FROM ex3_eventos WHERE event_ts IS NULL") == 0),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 4 · RN-03: o status atual
# MAGIC
# MAGIC A partir de `ex3_eventos`, deixe **uma linha por pedido**, com o evento mais recente.
# MAGIC Colunas: `order_id`, `status` e `status_desde` (a data desse evento). Empate na data: ganha o maior `event_id`.

# COMMAND ----------

sql_ex4 = """
SELECT
  order_id,
  status,
  event_ts AS status_desde
FROM ex3_eventos
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY event_ts DESC, event_id DESC) = 1
"""
criar_view("ex4_status_atual", sql_ex4)

# COMMAND ----------

conferir("Exercício 4", [
    ("a view existe", lambda: pronta("ex4_status_atual")),
    ("uma linha por pedido (1.500)", lambda: um("SELECT COUNT(*) FROM ex4_status_atual") == 1500 and um("SELECT COUNT(DISTINCT order_id) FROM ex4_status_atual") == 1500),
    ("pegou o mais recente, não o primeiro (quase nenhum 'criado')", lambda: um("SELECT COUNT(*) FROM ex4_status_atual WHERE status = 'criado'") == 106),
    ("1.052 pedidos entregues", lambda: um("SELECT COUNT(*) FROM ex4_status_atual WHERE status = 'entregue'") == 1052),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 5 · RN-04, RN-05 e RN-06: vendas por região e mês
# MAGIC
# MAGIC O resumo que a Marina pediu. A partir de `ex4_status_atual`, `bronze.pedidos` e `bronze.clientes`, uma linha por região e mês, com:
# MAGIC `regiao`, `mes` (o primeiro dia do mês da entrega, como `DATE`), `qtd_pedidos` e `valor_vendas`.
# MAGIC
# MAGIC - RN-04: só pedidos com status atual `entregue`.
# MAGIC - RN-05: o valor é o `valor_liquido`.
# MAGIC - RN-06: UF do cliente (em maiúsculas) → região do IBGE; sem UF → `'Não informada'`.
# MAGIC
# MAGIC | Região | UFs |
# MAGIC |---|---|
# MAGIC | Norte | AC, AM, AP, PA, RO, RR, TO |
# MAGIC | Nordeste | AL, BA, CE, MA, PB, PE, PI, RN, SE |
# MAGIC | Centro-Oeste | DF, GO, MS, MT |
# MAGIC | Sudeste | ES, MG, RJ, SP |
# MAGIC | Sul | PR, RS, SC |
# MAGIC
# MAGIC **Dica:** `CAST(date_trunc('MONTH', status_desde) AS DATE)` dá o primeiro dia do mês.

# COMMAND ----------

sql_ex5 = """
WITH concluidos AS (
  SELECT
    CASE
      WHEN upper(trim(c.uf)) IN ('AC','AM','AP','PA','RO','RR','TO')           THEN 'Norte'
      WHEN upper(trim(c.uf)) IN ('AL','BA','CE','MA','PB','PE','PI','RN','SE') THEN 'Nordeste'
      WHEN upper(trim(c.uf)) IN ('DF','GO','MS','MT')                          THEN 'Centro-Oeste'
      WHEN upper(trim(c.uf)) IN ('ES','MG','RJ','SP')                          THEN 'Sudeste'
      WHEN upper(trim(c.uf)) IN ('PR','RS','SC')                               THEN 'Sul'
      ELSE 'Não informada'
    END AS regiao,
    CAST(date_trunc('MONTH', s.status_desde) AS DATE) AS mes,
    p.valor_liquido
  FROM ex4_status_atual s
  JOIN bronze.pedidos  p ON p.order_id = s.order_id
  JOIN bronze.clientes c ON c.customer_id = p.customer_id
  WHERE s.status = 'entregue'
)
SELECT regiao, mes, COUNT(*) AS qtd_pedidos, ROUND(SUM(valor_liquido), 2) AS valor_vendas
FROM concluidos
GROUP BY regiao, mes
"""
criar_view("ex5_vendas", sql_ex5)

# COMMAND ----------

conferir("Exercício 5", [
    ("a view existe", lambda: pronta("ex5_vendas")),
    ("17 linhas (região × mês)", lambda: um("SELECT COUNT(*) FROM ex5_vendas") == 17),
    ("1.052 pedidos no total", lambda: um("SELECT SUM(qtd_pedidos) FROM ex5_vendas") == 1052),
    ("R$ 2.302.177,12 em vendas (valor líquido)", lambda: abs(float(um("SELECT SUM(valor_vendas) FROM ex5_vendas")) - 2302177.12) < 0.05),
    ("4 pedidos em 'Não informada' e nenhuma região nula",
        lambda: um("SELECT SUM(qtd_pedidos) FROM ex5_vendas WHERE regiao = 'Não informada'") == 4
                and um("SELECT COUNT(*) FROM ex5_vendas WHERE regiao IS NULL") == 0),
    ("Sudeste em setembro: 210 pedidos", lambda: um("SELECT qtd_pedidos FROM ex5_vendas WHERE regiao = 'Sudeste' AND mes = DATE'2026-09-01'") == 210),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Desafios extras (sem gabarito)
# MAGIC
# MAGIC 1. Some a coluna `ticket_medio` (valor ÷ pedidos) no exercício 5.
# MAGIC 2. Quantos pedidos foram cancelados **depois** de passar por `enviado`? Escreva a consulta.
# MAGIC 3. Troque a RN-03 por "o primeiro evento" em vez do mais recente. Quantos entregues sobram? Por que esse número mente?
