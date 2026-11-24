# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 3 · Teste: as camadas seguem o contrato?
# MAGIC
# MAGIC Confere as tabelas que a aula 3 criou. Se algo falhar, o notebook termina em vermelho e diz o quê.
# MAGIC
# MAGIC | Teste | Pergunta | Pega qual erro |
# MAGIC |---|---|---|
# MAGIC | bronze completa | a bronze tem todas as linhas da fonte? | carga incompleta |
# MAGIC | quarentena | foram 12 sem data e 5 órfãos? | RN-07 esquecida |
# MAGIC | status normalizado | só existem os 5 status válidos? | RN-01 incompleta |
# MAGIC | sem duplicados | cada `event_id` aparece uma vez? | RN-02 pela chave errada |
# MAGIC | um status por pedido | cada `order_id` aparece uma vez em `status_atual`? | RN-03 |
# MAGIC | concluídos | 1.052 pedidos concluídos? | RN-04 (e todas as anteriores) |
# MAGIC | valor | soma das vendas = R$ 2.302.177,12? | RN-05 com valor bruto |
# MAGIC | região | nenhuma venda com região nula, 4 em `Não informada`? | RN-06 |
# MAGIC | reconciliação | soma da gold por região = soma de `pedidos_concluidos`? | linha perdida no `GROUP BY` |

# COMMAND ----------

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
spark.sql(f"USE CATALOG {CAT}")

def um(sql):
    return spark.sql(sql).first()[0]

testes = [
    ("bronze completa", "SELECT (SELECT COUNT(*) FROM bronze.clientes) = 500 AND (SELECT COUNT(*) FROM bronze.produtos) = 60 "
                        "AND (SELECT COUNT(*) FROM bronze.pedidos) = 1500 AND (SELECT COUNT(*) FROM bronze.eventos_pedido) = 5416"),
    ("quarentena (RN-07)", "SELECT SUM(CASE WHEN motivo = 'sem_data' THEN 1 ELSE 0 END) = 12 "
                           "AND SUM(CASE WHEN motivo = 'pedido_inexistente' THEN 1 ELSE 0 END) = 5 FROM silver.quarentena"),
    ("status normalizado (RN-01)", "SELECT COUNT(*) = 0 FROM silver.eventos_pedido "
                                   "WHERE status NOT IN ('criado', 'pago', 'enviado', 'entregue', 'cancelado')"),
    ("sem duplicados (RN-02)", "SELECT COUNT(*) = COUNT(DISTINCT event_id) AND COUNT(*) = 5226 FROM silver.eventos_pedido"),
    ("um status por pedido (RN-03)", "SELECT COUNT(*) = COUNT(DISTINCT order_id) AND COUNT(*) = 1500 FROM silver.status_atual"),
    ("concluídos (RN-04)", "SELECT COUNT(*) = 1052 FROM gold.pedidos_concluidos"),
    ("valor (RN-05)", "SELECT ROUND(SUM(valor_venda), 2) = 2302177.12 FROM gold.pedidos_concluidos"),
    ("região (RN-06)", "SELECT SUM(CASE WHEN regiao IS NULL THEN 1 ELSE 0 END) = 0 "
                       "AND SUM(CASE WHEN regiao = 'Não informada' THEN quantidade_pedidos ELSE 0 END) = 4 FROM gold.vendas_por_regiao"),
    ("reconciliação", "SELECT (SELECT ROUND(SUM(valor_vendas), 2) FROM gold.vendas_por_regiao) "
                      "= (SELECT ROUND(SUM(valor_venda), 2) FROM gold.pedidos_concluidos)"),
]

resultados, falhas = [], []
for nome, sql in testes:
    try:
        ok = bool(um(sql))
        detalhe = ""
    except Exception as e:
        ok, detalhe = False, f"{type(e).__name__}: {str(e)[:150]}"
    resultados.append((nome, "OK" if ok else "FALHOU", detalhe))
    if not ok:
        falhas.append(nome)

display(spark.createDataFrame(resultados, "teste string, resultado string, detalhe string"))
assert not falhas, f"Testes que falharam: {falhas}"
print("Camadas conferidas: todos os testes OK")
