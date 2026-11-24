# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 3 · Transformação com regra rastreável
# MAGIC
# MAGIC **O que esta etapa faz:** lê o JSON cru da landing e constrói as camadas bronze → silver → gold.
# MAGIC Cada regra do [contrato de dados](../../docs/contrato_de_dados.md) vira um trecho de código **marcado com o número dela** (`-- RN-02`).
# MAGIC
# MAGIC **Por quê:** quando alguém perguntar "de onde vem esse número?", a resposta tem que caber numa frase:
# MAGIC "da RN-04, que está nesta linha, e o teste da aula 4 prova". Isso é **rastreabilidade**.
# MAGIC
# MAGIC | Regra | O que diz | Onde fica |
# MAGIC |---|---|---|
# MAGIC | RN-07 | evento sem data ou de pedido que não existe vai para a quarentena | `silver.quarentena` |
# MAGIC | RN-01 | status escrito de jeitos diferentes vira um só (`Entregue`, `delivered` → `entregue`) | `silver.eventos_pedido` |
# MAGIC | RN-02 | evento duplicado (mesmo `event_id`) conta uma vez | `silver.eventos_pedido` |
# MAGIC | RN-03 | status atual = evento mais recente do pedido | `silver.status_atual` |
# MAGIC | RN-04 | pedido concluído = status atual `entregue` | `gold.pedidos_concluidos` |
# MAGIC | RN-05 | valor da venda = `valor_liquido` | `gold.pedidos_concluidos` |
# MAGIC | RN-06 | região = UF do cliente → região do IBGE; sem UF → `Não informada` | `silver.clientes` e `gold.vendas_por_regiao` |
# MAGIC
# MAGIC RN-08 e RN-09 (quem vê o quê) ficam para a aula 5.
# MAGIC
# MAGIC Antes: rode a aula 2 (ou o plano B) para ter a landing completa, com o mesmo catálogo.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 0 · Parâmetros
# MAGIC O `USE CATALOG` faz as células SQL abaixo usarem o catálogo do widget. Assim, no SQL, basta escrever `silver.status_atual`.

# COMMAND ----------

import json
from pyspark.sql import functions as F

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
LANDING = f"/Volumes/{CAT}/raw/landing"
spark.sql(f"USE CATALOG {CAT}")
print(f"Catálogo: {CAT} | Landing: {LANDING}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 1 · Bronze: fiel à origem, com metadados
# MAGIC
# MAGIC A bronze **não aplica regra nenhuma**. Ela só transforma o JSON cru em tabela e anota de onde veio cada linha:
# MAGIC
# MAGIC | Coluna | Para quê |
# MAGIC |---|---|
# MAGIC | `_carga_id` | qual carga da aula 2 trouxe a linha |
# MAGIC | `_arquivo` | de qual página (arquivo) ela saiu |
# MAGIC | `_ingerido_em` | quando entrou na bronze |
# MAGIC
# MAGIC Lemos só a carga **completa** mais recente de cada tabela (a que tem `_manifesto.json`), do mesmo jeito que o teste da aula 2.

# COMMAND ----------

def ultima_carga_completa(tabela):
    """Pasta da carga mais recente que tem manifesto (decidida pela data do manifesto)."""
    cargas = [a.path.replace("dbfs:", "").rstrip("/") for a in dbutils.fs.ls(f"{LANDING}/{tabela}") if a.name.startswith("carga_")]
    completas = {}
    for pasta in cargas:
        if any(a.name == "_manifesto.json" for a in dbutils.fs.ls(pasta)):
            with open(f"{pasta}/_manifesto.json") as f:
                completas[pasta] = json.load(f)
    if not completas:
        raise RuntimeError(f"{tabela}: nenhuma carga completa na landing. Rode a aula 2 (ou o plano B) antes.")
    return max(completas.items(), key=lambda kv: kv[1]["inicio_utc"])

def carregar_bronze(tabela):
    pasta, manifesto = ultima_carga_completa(tabela)
    df = (spark.read.json(f"{pasta}/pagina_*.json")
          .select(F.explode("rows").alias("r"), F.col("_metadata.file_path").alias("_arquivo"))
          .select("r.row.*", F.col("r.row_idx").alias("_row_idx"), "_arquivo")
          .withColumn("_carga_id", F.lit(manifesto["carga_id"]))
          .withColumn("_ingerido_em", F.current_timestamp()))
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"bronze.{tabela}")
    return df.count(), manifesto["carga_id"]

for tabela in ["clientes", "produtos", "pedidos", "eventos_pedido"]:
    linhas, carga = carregar_bronze(tabela)
    print(f"bronze.{tabela}: {linhas} linhas (carga {carga})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 2 · Olhando a bagunça antes de arrumar
# MAGIC Quantos jeitos diferentes de escrever o status existem na fonte?

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT status, COUNT(*) AS eventos
# MAGIC FROM bronze.eventos_pedido
# MAGIC GROUP BY status
# MAGIC ORDER BY eventos DESC

# COMMAND ----------

# MAGIC %md
# MAGIC Dez grafias para cinco status. Se a gente filtrar `status = 'entregue'`, perde `Entregue`, `ENTREGUE` e `delivered`.
# MAGIC Esse é o número 946 da pessoa A, lá da aula 1.
# MAGIC
# MAGIC ## Passo 3 · RN-07: a quarentena vem primeiro
# MAGIC
# MAGIC Evento sem data não tem como entrar no "mais recente". Evento de pedido que não existe não tem a quem pertencer.
# MAGIC Os dois saem do caminho **antes** de qualquer outra regra, mas não somem: vão para `silver.quarentena`, com o motivo.
# MAGIC
# MAGIC Por que antes? Um evento duplicado chegou com uma cópia **com** data e outra **sem**. Se a gente deduplicar primeiro,
# MAGIC pode sobrar justo a cópia sem data, e o pedido perde o status. A ordem das regras também é regra.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- RN-07: evento sem data ou de pedido inexistente → quarentena (não some: fica guardado com o motivo)
# MAGIC CREATE OR REPLACE TABLE silver.quarentena AS
# MAGIC SELECT
# MAGIC   e.event_id,
# MAGIC   e.order_id,
# MAGIC   e.status,
# MAGIC   e.event_ts AS event_timestamp,
# MAGIC   CASE WHEN e.event_ts IS NULL THEN 'sem_data' ELSE 'pedido_inexistente' END AS motivo,
# MAGIC   'RN-07' AS regra,
# MAGIC   e._carga_id
# MAGIC FROM bronze.eventos_pedido e
# MAGIC LEFT JOIN bronze.pedidos p ON p.order_id = e.order_id
# MAGIC WHERE e.event_ts IS NULL OR p.order_id IS NULL

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT motivo, COUNT(*) AS eventos FROM silver.quarentena GROUP BY motivo

# COMMAND ----------

# MAGIC %md
# MAGIC Esperado: `sem_data` 12 e `pedido_inexistente` 5.
# MAGIC
# MAGIC ## Erro de propósito · Deduplicar pela coluna errada
# MAGIC
# MAGIC "Sem duplicidade" parece querer dizer "um pedido por linha". Então vamos deduplicar por `order_id`…

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ERRADO DE PROPÓSITO: deduplicando por order_id em vez de event_id
# MAGIC WITH dedup_errado AS (
# MAGIC   SELECT e.*
# MAGIC   FROM bronze.eventos_pedido e
# MAGIC   JOIN bronze.pedidos p ON p.order_id = e.order_id   -- já sem o que foi para a quarentena
# MAGIC   WHERE e.event_ts IS NOT NULL
# MAGIC   QUALIFY ROW_NUMBER() OVER (PARTITION BY e.order_id ORDER BY e.event_ts) = 1
# MAGIC )
# MAGIC SELECT
# MAGIC   COUNT(*) AS linhas,
# MAGIC   SUM(CASE WHEN lower(status) IN ('entregue', 'delivered') THEN 1 ELSE 0 END) AS entregues
# MAGIC FROM dedup_errado

# COMMAND ----------

# MAGIC %md
# MAGIC Sobra uma linha por pedido, sim. Mas sobra o **primeiro** evento de cada um (quase sempre `criado`), e **nenhum** pedido aparece como entregue.
# MAGIC Mais de 3.700 eventos sumiram sem nenhum erro na tela.
# MAGIC
# MAGIC Duplicidade, no contrato, é **o mesmo evento repetido** (pergunta 3 → RN-02). A chave é `event_id`.
# MAGIC
# MAGIC ## Passo 4 · RN-01 e RN-02: `silver.eventos_pedido`

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE silver.eventos_pedido AS
# MAGIC WITH validos AS (
# MAGIC   -- RN-07: só entra o que não foi para a quarentena
# MAGIC   SELECT e.*
# MAGIC   FROM bronze.eventos_pedido e
# MAGIC   JOIN bronze.pedidos p ON p.order_id = e.order_id
# MAGIC   WHERE e.event_ts IS NOT NULL
# MAGIC ),
# MAGIC normalizados AS (
# MAGIC   SELECT
# MAGIC     event_id,
# MAGIC     order_id,
# MAGIC     -- RN-01: uma grafia por status
# MAGIC     CASE lower(trim(status))
# MAGIC       WHEN 'delivered' THEN 'entregue'
# MAGIC       WHEN 'canceled'  THEN 'cancelado'
# MAGIC       ELSE lower(trim(status))
# MAGIC     END AS status,
# MAGIC     status AS status_original,
# MAGIC     CAST(event_ts AS TIMESTAMP) AS event_timestamp,  -- nome claro a partir da silver
# MAGIC     canal,
# MAGIC     _carga_id
# MAGIC   FROM validos
# MAGIC )
# MAGIC SELECT *
# MAGIC FROM normalizados
# MAGIC -- RN-02: mesmo event_id = mesmo evento → fica uma linha só
# MAGIC QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY event_timestamp) = 1

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT status, COUNT(*) AS eventos, COUNT(DISTINCT status_original) AS grafias_na_fonte
# MAGIC FROM silver.eventos_pedido
# MAGIC GROUP BY status
# MAGIC ORDER BY eventos DESC

# COMMAND ----------

# MAGIC %md
# MAGIC Cinco status, nenhuma grafia perdida. Guardamos a original em `status_original`: se alguém duvidar da RN-01, dá para conferir.
# MAGIC
# MAGIC ## Passo 5 · RN-03: `silver.status_atual`
# MAGIC Um pedido passa por vários status. O que vale é o mais recente. Se dois eventos tiverem a mesma hora, ganha o maior `event_id` (premissa 2 do contrato).

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE silver.status_atual AS
# MAGIC SELECT
# MAGIC   order_id,
# MAGIC   status,
# MAGIC   event_timestamp AS status_desde,
# MAGIC   event_id
# MAGIC FROM silver.eventos_pedido
# MAGIC -- RN-03: status atual = evento mais recente do pedido (empate: maior event_id)
# MAGIC QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY event_timestamp DESC, event_id DESC) = 1

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   COUNT(*)                 AS linhas,
# MAGIC   COUNT(DISTINCT order_id) AS pedidos,
# MAGIC   SUM(CASE WHEN status = 'entregue' THEN 1 ELSE 0 END) AS entregues
# MAGIC FROM silver.status_atual

# COMMAND ----------

# MAGIC %md
# MAGIC Esperado: 1.500 linhas, 1.500 pedidos (uma linha por pedido) e **1.052 entregues**.
# MAGIC
# MAGIC ## Passo 6 · Clientes e pedidos na silver
# MAGIC Em clientes, a UF vem às vezes em minúsculas e às vezes vazia. A RN-06 começa aqui: UF em maiúsculas → região do IBGE.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE silver.clientes AS
# MAGIC SELECT
# MAGIC   customer_id,
# MAGIC   nome,
# MAGIC   email,
# MAGIC   telefone,
# MAGIC   cidade,
# MAGIC   upper(trim(uf)) AS uf,
# MAGIC   -- RN-06: UF → região do IBGE; sem UF → 'Não informada'
# MAGIC   CASE
# MAGIC     WHEN upper(trim(uf)) IN ('AC', 'AM', 'AP', 'PA', 'RO', 'RR', 'TO')                   THEN 'Norte'
# MAGIC     WHEN upper(trim(uf)) IN ('AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE')       THEN 'Nordeste'
# MAGIC     WHEN upper(trim(uf)) IN ('DF', 'GO', 'MS', 'MT')                                     THEN 'Centro-Oeste'
# MAGIC     WHEN upper(trim(uf)) IN ('ES', 'MG', 'RJ', 'SP')                                     THEN 'Sudeste'
# MAGIC     WHEN upper(trim(uf)) IN ('PR', 'RS', 'SC')                                           THEN 'Sul'
# MAGIC     ELSE 'Não informada'
# MAGIC   END AS regiao,
# MAGIC   CAST(cadastrado_em AS TIMESTAMP) AS cadastrado_em
# MAGIC FROM bronze.clientes

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE silver.pedidos AS
# MAGIC SELECT
# MAGIC   order_id,
# MAGIC   customer_id,
# MAGIC   CAST(criado_em AS TIMESTAMP) AS criado_em,
# MAGIC   itens,
# MAGIC   valor_bruto,
# MAGIC   valor_liquido
# MAGIC FROM bronze.pedidos

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 7 · Gold: o que a Marina pediu
# MAGIC
# MAGIC `gold.pedidos_concluidos` tem um pedido por linha, para detalhar. `gold.vendas_por_regiao` é o resumo do chamado.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE gold.pedidos_concluidos AS
# MAGIC SELECT
# MAGIC   s.order_id,
# MAGIC   p.customer_id,
# MAGIC   c.nome,
# MAGIC   c.email,
# MAGIC   c.telefone,
# MAGIC   c.uf,
# MAGIC   c.regiao,
# MAGIC   s.status_desde AS entregue_em,
# MAGIC   CAST(date_trunc('MONTH', s.status_desde) AS DATE) AS mes,
# MAGIC   p.valor_liquido AS valor_venda              -- RN-05: venda = valor com desconto
# MAGIC FROM silver.status_atual s
# MAGIC JOIN silver.pedidos  p ON p.order_id = s.order_id
# MAGIC JOIN silver.clientes c ON c.customer_id = p.customer_id
# MAGIC WHERE s.status = 'entregue'                    -- RN-04: concluído = status atual entregue
# MAGIC   AND s.status_desde >= '2026-08-01'           -- premissa 6: entregas de ago a out/2026
# MAGIC   AND s.status_desde <  '2026-11-01'

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE gold.vendas_por_regiao AS
# MAGIC SELECT
# MAGIC   regiao,                                       -- RN-06 (calculada em silver.clientes)
# MAGIC   mes,
# MAGIC   COUNT(*)                               AS quantidade_pedidos,
# MAGIC   ROUND(SUM(valor_venda), 2)             AS valor_vendas,
# MAGIC   ROUND(SUM(valor_venda) / COUNT(*), 2)  AS ticket_medio
# MAGIC FROM gold.pedidos_concluidos
# MAGIC GROUP BY regiao, mes

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM gold.vendas_por_regiao ORDER BY regiao, mes

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 8 · Os três números da aula 1, agora com código
# MAGIC Lembra das três pessoas que receberam o mesmo chamado? Aqui estão as três contas, lado a lado.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'A · status = ''entregue'' exato'              AS quem, COUNT(*) AS pedidos_concluidos
# MAGIC FROM bronze.eventos_pedido WHERE status = 'entregue'
# MAGIC UNION ALL
# MAGIC SELECT 'B · ignorando maiúsculas, com duplicados',   COUNT(*)
# MAGIC FROM bronze.eventos_pedido WHERE lower(status) = 'entregue'
# MAGIC UNION ALL
# MAGIC SELECT 'C · contrato (RN-01, RN-02, RN-03, RN-07)',  COUNT(*)
# MAGIC FROM gold.pedidos_concluidos

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 9 · Checkpoint: cada regra e o número que prova
# MAGIC Esta tabela é o resumo da aula: a regra, onde ela mora e o número que mostra que ela foi aplicada.

# COMMAND ----------

def um(sql):
    return spark.sql(sql).first()[0]

checkpoint = [
    ("RN-07", "silver.quarentena", "eventos na quarentena", um("SELECT COUNT(*) FROM silver.quarentena"), 17),
    ("RN-01", "silver.eventos_pedido", "status diferentes", um("SELECT COUNT(DISTINCT status) FROM silver.eventos_pedido"), 5),
    ("RN-02", "silver.eventos_pedido", "eventos (sem duplicados)", um("SELECT COUNT(*) FROM silver.eventos_pedido"), 5226),
    ("RN-03", "silver.status_atual", "linhas (1 por pedido)", um("SELECT COUNT(*) FROM silver.status_atual"), 1500),
    ("RN-04", "gold.pedidos_concluidos", "pedidos concluídos", um("SELECT COUNT(*) FROM gold.pedidos_concluidos"), 1052),
    ("RN-05", "gold.pedidos_concluidos", "valor das vendas (R$)", float(um("SELECT ROUND(SUM(valor_venda), 2) FROM gold.pedidos_concluidos")), 2302177.12),
    ("RN-06", "gold.vendas_por_regiao", "pedidos em 'Não informada'", um("SELECT SUM(quantidade_pedidos) FROM gold.vendas_por_regiao WHERE regiao = 'Não informada'"), 4),
]
display(spark.createDataFrame(
    [(rn, onde, o_que, float(obtido), float(esperado), "OK" if abs(float(obtido) - esperado) < 0.01 else "CONFERIR")
     for rn, onde, o_que, obtido, esperado in checkpoint],
    "regra string, tabela string, o_que string, obtido double, esperado double, resultado string"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 10 · O histórico da tabela e a volta no tempo
# MAGIC
# MAGIC Toda tabela Delta guarda um **histórico**: cada escrita vira uma versão nova, com data, operação e quem fez
# MAGIC ([doc](https://docs.databricks.com/aws/en/delta/history)). Isso ajuda a responder outra pergunta de reunião:
# MAGIC "esse número mudou? quando? quem mexeu?".
# MAGIC
# MAGIC O exemplo usa `silver.status_atual`, de onde sai o 1.052. (Por que não a gold? Na aula 5 a gold ganha filtro de linha,
# MAGIC e tabela com filtro de linha **não aceita volta no tempo**. Assim este passo funciona mesmo se você refizer a aula 3 depois.)

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE HISTORY silver.status_atual

# COMMAND ----------

# MAGIC %md
# MAGIC Agora um **acidente de propósito**: alguém roda um `UPDATE` sem querer e marca como `cancelado` todos os pedidos
# MAGIC entregues em setembro. O 1.052 cai, e nenhuma célula fica vermelha.

# COMMAND ----------

versao_boa = spark.sql("DESCRIBE HISTORY silver.status_atual").first()["version"]
spark.sql("""UPDATE silver.status_atual SET status = 'cancelado'
             WHERE status = 'entregue' AND status_desde >= '2026-09-01' AND status_desde < '2026-10-01'""")   # ACIDENTE DE PROPÓSITO

display(spark.sql(f"""
    SELECT
      (SELECT COUNT(*) FROM silver.status_atual VERSION AS OF {versao_boa} WHERE status = 'entregue') AS entregues_antes,
      (SELECT COUNT(*) FROM silver.status_atual WHERE status = 'entregue')                            AS entregues_agora"""))
print(f"Versão boa (antes do acidente): {versao_boa}")

# COMMAND ----------

# MAGIC %md
# MAGIC `VERSION AS OF` lê a tabela **como ela era** naquela versão: é a *time travel* do Delta.
# MAGIC E o `RESTORE` volta a tabela inteira para lá. O próprio `RESTORE` vira uma versão nova no histórico: nada é apagado.

# COMMAND ----------

spark.sql(f"RESTORE TABLE silver.status_atual TO VERSION AS OF {versao_boa}")
print("Entregues depois do RESTORE:", spark.sql("SELECT COUNT(*) FROM silver.status_atual WHERE status = 'entregue'").first()[0])
display(spark.sql("SELECT version, timestamp, operation FROM (DESCRIBE HISTORY silver.status_atual) ORDER BY version DESC LIMIT 5"))

# COMMAND ----------

# MAGIC %md
# MAGIC Esperado: `entregues_antes` = 1052 e `entregues_agora` menor; depois do `RESTORE`, 1052 de novo. No histórico, as versões
# MAGIC mais recentes são o `RESTORE`, o `UPDATE` e a criação da tabela (pode aparecer também um `OPTIMIZE` feito pelo próprio
# MAGIC Databricks). Se você já rodou a aula antes, aparecem versões mais antigas: o `CREATE OR REPLACE` mantém o histórico.
# MAGIC
# MAGIC **Limite:** a volta no tempo depende dos arquivos antigos. O `VACUUM` apaga arquivos que não são mais usados,
# MAGIC depois do período de retenção, e aí as versões antigas deixam de ser lidas
# MAGIC ([doc](https://docs.databricks.com/aws/en/delta/history#data-retention)).
