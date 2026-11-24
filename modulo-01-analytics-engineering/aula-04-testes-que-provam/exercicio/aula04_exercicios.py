# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 4 · Exercícios: escreva testes que provam a regra
# MAGIC
# MAGIC Na aula, cada regra do contrato ganhou um teste. Aqui é você quem escreve:
# MAGIC
# MAGIC | # | Exercício | Tipo | Regra |
# MAGIC |---|---|---|---|
# MAGIC | 1 | Um status por pedido | unicidade | RN-03 |
# MAGIC | 2 | Só os 5 status do contrato | domínio | RN-01 |
# MAGIC | 3 | O resumo bate com o detalhe | reconciliação | RN-05 |
# MAGIC | 4 | Todo concluído está entregue | regra de negócio | RN-04 |
# MAGIC | 5 | Barrar na entrada | constraint | RN-05 |
# MAGIC
# MAGIC **Como funciona:** nos exercícios 1 a 4, escreva um `SELECT` que devolve **um número: quantas linhas violam a regra**.
# MAGIC A célula **Conferir** roda o seu teste duas vezes:
# MAGIC
# MAGIC - na tabela de verdade, onde ele tem que dar **0** (passou);
# MAGIC - numa cópia **sabotada** (com um problema colocado de propósito), onde ele tem que dar **mais que 0** (pegou).
# MAGIC
# MAGIC Teste que não pega a sabotagem não está testando nada. Use exatamente os nomes de tabela pedidos no enunciado:
# MAGIC é assim que a conferência troca a tabela pela cópia sabotada.
# MAGIC
# MAGIC Antes: rode a aula 3 com o mesmo catálogo. O gabarito está em `solucao/aula04_exercicios_gabarito`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Preparação (só rodar)
# MAGIC Cria as cópias sabotadas (views temporárias: não mexem nas tabelas da aula) e a tabela do exercício 5.

# COMMAND ----------

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
spark.sql(f"USE CATALOG {CAT}")

SABOTAGENS = {
    # um pedido aparece duas vezes
    "sab_status_atual": """
        SELECT * FROM silver.status_atual
        UNION ALL
        SELECT * FROM (SELECT * FROM silver.status_atual ORDER BY order_id LIMIT 1)""",
    # um status com maiúscula e um status vazio
    "sab_eventos_pedido": """
        SELECT * FROM silver.eventos_pedido
        UNION ALL
        SELECT event_id || '-x', order_id, 'Entregue', status_original, event_timestamp, canal, _carga_id
        FROM (SELECT * FROM silver.eventos_pedido ORDER BY event_id LIMIT 1)
        UNION ALL
        SELECT event_id || '-y', order_id, CAST(NULL AS STRING), status_original, event_timestamp, canal, _carga_id
        FROM (SELECT * FROM silver.eventos_pedido ORDER BY event_id LIMIT 1)""",
    # uma linha do resumo sumiu
    "sab_vendas_por_regiao": """
        SELECT * FROM gold.vendas_por_regiao
        QUALIFY ROW_NUMBER() OVER (ORDER BY regiao, mes) > 1""",
    # um pedido concluído passou a ter status atual 'enviado'
    "sab4_status_atual": """
        SELECT order_id,
               CASE WHEN order_id = (SELECT MIN(order_id) FROM gold.pedidos_concluidos) THEN 'enviado' ELSE status END AS status,
               status_desde, event_id
        FROM silver.status_atual""",
}
for nome, sql in SABOTAGENS.items():
    spark.sql(f"CREATE OR REPLACE TEMP VIEW {nome} AS {sql}")

# Exercício 5: uma cópia de silver.pedidos só para você pôr a constraint
spark.sql("CREATE OR REPLACE TABLE qualidade.ex04_pedidos AS SELECT * FROM silver.pedidos")
print("Preparação pronta: 4 cópias sabotadas e qualidade.ex04_pedidos")

# COMMAND ----------

def um(sql):
    return spark.sql(sql).first()[0]

def pendente(sql):
    return not sql.strip() or "✏️" in sql

def conferir_teste(exercicio, sql, trocas):
    """Roda o teste na tabela de verdade (tem que dar 0) e na cópia sabotada (tem que dar > 0)."""
    if pendente(sql):
        print(f"⏳ {exercicio}: escreva o SELECT e rode de novo.")
        return
    sabotado = sql
    for tabela, copia in trocas.items():
        sabotado = sabotado.replace(tabela, copia)
    casos = []
    try:
        real = um(sql)
        casos.append(("na tabela de verdade deu 0 (passou)", real == 0, f"deu {real}"))
        if sabotado == sql:
            casos.append(("usa a tabela pedida no enunciado", False, f"o SQL precisa ler {', '.join(trocas)}"))
        else:
            sab = um(sabotado)
            casos.append(("na cópia sabotada deu mais que 0 (pegou)", sab is not None and sab > 0, f"deu {sab}"))
    except Exception as e:
        casos.append(("o SQL roda", False, f"{type(e).__name__}: {str(e).splitlines()[0][:160]}"))
    tudo_certo = True
    for descricao, passou, detalhe in casos:
        print(("✅ " if passou else "❌ ") + descricao + ("" if passou else f"  →  {detalhe}"))
        tudo_certo = tudo_certo and passou
    print(f"\n🎉 {exercicio}: tudo certo!" if tudo_certo else f"\n{exercicio}: ainda não. Releia a dica e tente de novo.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 1 · RN-03: um status por pedido (unicidade)
# MAGIC
# MAGIC Em `silver.status_atual`, cada `order_id` tem que aparecer **uma vez só**.
# MAGIC Escreva um `SELECT` que devolva quantas linhas sobram além de uma por pedido.
# MAGIC
# MAGIC **Dica:** compare `COUNT(*)` com `COUNT(DISTINCT order_id)`.

# COMMAND ----------

teste_ex1 = """
-- ✏️ Exercício 1: escreva o SELECT aqui (use silver.status_atual)
"""
conferir_teste("Exercício 1", teste_ex1, {"silver.status_atual": "sab_status_atual"})

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 2 · RN-01: só os 5 status do contrato (domínio)
# MAGIC
# MAGIC Em `silver.eventos_pedido`, o `status` só pode ser `criado`, `pago`, `enviado`, `entregue` ou `cancelado`.
# MAGIC Conte as linhas que fogem disso.
# MAGIC
# MAGIC **Dica:** a cópia sabotada tem **duas** linhas ruins: um `Entregue` com maiúscula e um status **vazio** (`NULL`).
# MAGIC `NOT IN (...)` sozinho não pega o `NULL`. Lembra do erro de propósito da aula?

# COMMAND ----------

teste_ex2 = """
-- ✏️ Exercício 2: escreva o SELECT aqui (use silver.eventos_pedido)
"""
conferir_teste("Exercício 2", teste_ex2, {"silver.eventos_pedido": "sab_eventos_pedido"})

# COMMAND ----------

# Conferência extra do exercício 2: o teste tem que pegar as DUAS linhas ruins, inclusive o NULL
if not pendente(teste_ex2):
    sab = um(teste_ex2.replace("silver.eventos_pedido", "sab_eventos_pedido"))
    print("✅ pegou as 2 linhas ruins, inclusive o NULL" if sab == 2
          else f"❌ pegou {sab} de 2 linhas ruins. Falta tratar o status NULL?")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 3 · RN-05: o resumo bate com o detalhe (reconciliação)
# MAGIC
# MAGIC A soma de `valor_vendas` em `gold.vendas_por_regiao` tem que ser igual à soma de `valor_venda` em `gold.pedidos_concluidos`.
# MAGIC Devolva **0** se bater (diferença menor que 1 centavo) e **1** se não bater.
# MAGIC
# MAGIC **Dica:** duas subconsultas, uma para cada soma, dentro de um `CASE WHEN ABS(... - ...) < 0.01 THEN 0 ELSE 1 END`.

# COMMAND ----------

teste_ex3 = """
-- ✏️ Exercício 3: escreva o SELECT aqui (use gold.vendas_por_regiao e gold.pedidos_concluidos)
"""
conferir_teste("Exercício 3", teste_ex3, {"gold.vendas_por_regiao": "sab_vendas_por_regiao"})

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 4 · RN-04: todo concluído está entregue (regra de negócio)
# MAGIC
# MAGIC Todo pedido de `gold.pedidos_concluidos` tem que estar com status atual `entregue` em `silver.status_atual`.
# MAGIC Conte os pedidos da gold cujo status atual **não** é `entregue`.
# MAGIC
# MAGIC **Dica:** `JOIN` das duas tabelas pelo `order_id` e um `WHERE` no status.

# COMMAND ----------

teste_ex4 = """
-- ✏️ Exercício 4: escreva o SELECT aqui (use gold.pedidos_concluidos e silver.status_atual)
"""
conferir_teste("Exercício 4", teste_ex4, {"silver.status_atual": "sab4_status_atual"})

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 5 · Barrar na entrada (constraint)
# MAGIC
# MAGIC Na tabela `qualidade.ex04_pedidos` (uma cópia de `silver.pedidos`, só sua), crie uma constraint chamada
# MAGIC `ex04_valor_positivo` que só aceite `valor_liquido` **maior que zero**.
# MAGIC
# MAGIC **Dica:** `ALTER TABLE <tabela> ADD CONSTRAINT <nome> CHECK (<condição>)`.
# MAGIC ([doc das constraints](https://docs.databricks.com/aws/en/tables/constraints))

# COMMAND ----------

comando_ex5 = """
-- ✏️ Exercício 5: escreva o ALTER TABLE aqui
"""
if pendente(comando_ex5):
    print("⏳ Exercício 5: escreva o ALTER TABLE e rode de novo.")
else:
    spark.sql("ALTER TABLE qualidade.ex04_pedidos DROP CONSTRAINT IF EXISTS ex04_valor_positivo")  # deixa rodar de novo
    spark.sql(comando_ex5)
    print("Comando aplicado. Agora rode a célula Conferir.")

# COMMAND ----------

if pendente(comando_ex5):
    print("⏳ Exercício 5: ainda falta escrever o ALTER TABLE.")
else:
    props = {r["key"]: r["value"] for r in spark.sql("SHOW TBLPROPERTIES qualidade.ex04_pedidos").collect()}
    tem = "delta.constraints.ex04_valor_positivo" in props
    print(("✅ " if tem else "❌ ") + "a constraint ex04_valor_positivo existe")
    try:
        spark.sql("INSERT INTO qualidade.ex04_pedidos SELECT order_id + 100000, customer_id, criado_em, itens, valor_bruto, -10.0 "
                  "FROM qualidade.ex04_pedidos LIMIT 1")
        print("❌ um pedido com valor -10 ENTROU: a condição está certa?")
        barrou = False
    except Exception as e:
        print("✅ um pedido com valor -10 foi recusado")
        barrou = True
    print("\n🎉 Exercício 5: tudo certo!" if tem and barrou else "\nExercício 5: ainda não. Releia a dica e tente de novo.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Desafios extras (sem gabarito)
# MAGIC
# MAGIC 1. Escreva o teste da RN-07: nenhum evento em `silver.eventos_pedido` sem data ou de pedido que não existe.
# MAGIC 2. Reconciliação por mês: a soma por mês da gold bate com a soma por mês dos pedidos concluídos?
# MAGIC 3. Rode a aula 3 de novo e depois `SHOW TBLPROPERTIES silver.status_atual`. A constraint da aula continua lá? Por quê?
