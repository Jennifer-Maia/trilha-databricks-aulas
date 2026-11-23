# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 4 · Testes que provam a regra
# MAGIC
# MAGIC **O que esta etapa faz:** transforma o checkpoint da aula 3 em **testes de verdade**: cada regra do
# MAGIC [contrato](../../docs/contrato_de_dados.md) ganha um teste com o mesmo número, o resultado fica salvo em
# MAGIC `qualidade.resultados_testes` (com histórico) e o notebook fica **vermelho** se algo falhar.
# MAGIC Depois, as **constraints do Delta** passam a barrar dado ruim na entrada.
# MAGIC
# MAGIC **Por quê:** o checkpoint da aula 3 só *mostra*. Teste de verdade precisa de três coisas:
# MAGIC
# MAGIC | O teste… | Para quê |
# MAGIC |---|---|
# MAGIC | **falha em vermelho** | ninguém precisa olhar uma tabela para perceber |
# MAGIC | **fica registrado** | dá para provar que passou ontem, e ver quando começou a falhar |
# MAGIC | **consegue falhar** | teste que nunca falha pode não estar testando nada |
# MAGIC
# MAGIC Antes: rode a aula 3 (as camadas bronze, silver e gold precisam existir), com o mesmo catálogo.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 0 · Parâmetros

# COMMAND ----------

import uuid
from datetime import datetime, timezone

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
spark.sql(f"USE CATALOG {CAT}")

def um(sql):
    return spark.sql(sql).first()[0]

print(f"Catálogo: {CAT}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 1 · Um teste é uma pergunta que procura o problema
# MAGIC
# MAGIC Todo teste desta aula segue o mesmo formato: um `SELECT` que **conta as linhas ruins**.
# MAGIC Zero linhas ruins = passou. Qualquer outro número = falhou, e o número já diz o tamanho do problema.
# MAGIC
# MAGIC | Tipo | Pergunta | Exemplo |
# MAGIC |---|---|---|
# MAGIC | unicidade | a chave aparece uma vez só? | `event_id` em `silver.eventos_pedido` |
# MAGIC | domínio | o valor está na lista permitida? | só 5 status |
# MAGIC | não nulo | o campo obrigatório veio? | região na gold |
# MAGIC | reconciliação | o total bate com a origem? | soma da gold = soma dos pedidos |
# MAGIC | regra de negócio | a regra do contrato vale linha a linha? | todo pedido concluído está `entregue` |
# MAGIC | regressão | o número de referência continua o mesmo? | 1.052 concluídos |
# MAGIC
# MAGIC Primeiro, um teste sozinho:

# COMMAND ----------

# MAGIC %sql
# MAGIC -- RN-02 · unicidade: quantos event_id aparecem mais de uma vez?
# MAGIC SELECT COUNT(*) - COUNT(DISTINCT event_id) AS linhas_ruins
# MAGIC FROM silver.eventos_pedido

# COMMAND ----------

# MAGIC %md
# MAGIC Esperado: `0`. Na bronze, a mesma pergunta dá 174: são os duplicados que a RN-02 tirou.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT COUNT(*) - COUNT(DISTINCT event_id) AS linhas_ruins
# MAGIC FROM bronze.eventos_pedido

# COMMAND ----------

# MAGIC %md
# MAGIC ## Erro de propósito · O teste que sempre passa
# MAGIC
# MAGIC RN-06: nenhuma venda pode ficar sem região. Um jeito comum de escrever esse teste:

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ERRADO DE PROPÓSITO: "= NULL" nunca é verdadeiro
# MAGIC SELECT COUNT(*) AS linhas_ruins
# MAGIC FROM gold.vendas_por_regiao
# MAGIC WHERE regiao = NULL

# COMMAND ----------

# MAGIC %md
# MAGIC Deu `0`. Passou! Mas passou porque a gold está certa, ou porque o teste não enxerga nada?
# MAGIC
# MAGIC Só tem um jeito de saber: **sabotar de propósito** e ver se o teste pega. Abaixo, uma cópia da gold
# MAGIC (uma *view temporária*, não mexe na tabela) com uma linha **sem região** colocada por nós.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW vendas_sabotada AS
# MAGIC SELECT * FROM gold.vendas_por_regiao
# MAGIC UNION ALL
# MAGIC SELECT NULL, DATE'2026-09-01', 1, 100.00, 100.00   -- uma venda sem região, de propósito

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   (SELECT COUNT(*) FROM vendas_sabotada WHERE regiao = NULL)  AS teste_errado,
# MAGIC   (SELECT COUNT(*) FROM vendas_sabotada WHERE regiao IS NULL) AS teste_certo

# COMMAND ----------

# MAGIC %md
# MAGIC `teste_errado` = 0 mesmo com a linha ruim lá dentro. `teste_certo` = 1: pegou.
# MAGIC
# MAGIC No SQL, `NULL` quer dizer "não sei". `regiao = NULL` pergunta "a região é igual a um valor que eu não sei?",
# MAGIC e a resposta é sempre "não sei", nunca "sim". Por isso o filtro não pega nenhuma linha.
# MAGIC Para nulo, é sempre `IS NULL` ou `IS NOT NULL`.
# MAGIC
# MAGIC **Lição:** antes de confiar num teste, veja ele falhar uma vez.
# MAGIC
# MAGIC ## Passo 2 · Os testes do contrato
# MAGIC
# MAGIC Cada teste tem o número da regra que ele prova. É a mesma tabela "Regras" do contrato, coluna "Como testar".

# COMMAND ----------

TESTES = [
    # (id, regra, tipo, tabela, SQL que conta as linhas ruins)
    ("T01", "RN-07", "regra de negócio", "silver.eventos_pedido",
     "SELECT COUNT(*) FROM silver.eventos_pedido "
     "WHERE event_ts IS NULL OR order_id NOT IN (SELECT order_id FROM silver.pedidos)"),
    ("T02", "RN-01", "domínio", "silver.eventos_pedido",
     "SELECT COUNT(*) FROM silver.eventos_pedido "
     "WHERE status IS NULL OR status NOT IN ('criado', 'pago', 'enviado', 'entregue', 'cancelado')"),
    ("T03", "RN-02", "unicidade", "silver.eventos_pedido",
     "SELECT COUNT(*) - COUNT(DISTINCT event_id) FROM silver.eventos_pedido"),
    ("T04", "RN-03", "unicidade", "silver.status_atual",
     "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM silver.status_atual"),
    ("T05", "RN-04", "regra de negócio", "gold.pedidos_concluidos",
     "SELECT COUNT(*) FROM gold.pedidos_concluidos g JOIN silver.status_atual s ON s.order_id = g.order_id "
     "WHERE s.status <> 'entregue'"),
    ("T06", "RN-05", "reconciliação", "gold.pedidos_concluidos",
     "SELECT COUNT(*) FROM gold.pedidos_concluidos g JOIN silver.pedidos p ON p.order_id = g.order_id "
     "WHERE g.valor_venda <> p.valor_liquido"),
    ("T07", "RN-06", "não nulo", "gold.vendas_por_regiao",
     "SELECT COUNT(*) FROM gold.vendas_por_regiao WHERE regiao IS NULL"),
    ("T08", "RN-05", "reconciliação", "gold.vendas_por_regiao",
     "SELECT CASE WHEN ABS((SELECT SUM(valor_vendas) FROM gold.vendas_por_regiao) "
     "- (SELECT SUM(valor_venda) FROM gold.pedidos_concluidos)) < 0.01 THEN 0 ELSE 1 END"),
    ("T09", "RN-04", "regressão", "gold.pedidos_concluidos",
     "SELECT ABS(COUNT(*) - 1052) FROM gold.pedidos_concluidos"),
]
print(f"{len(TESTES)} testes, cobrindo {len({t[1] for t in TESTES})} regras")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 3 · Rodar e guardar o resultado
# MAGIC
# MAGIC A tabela `qualidade.resultados_testes` é criada uma vez e **recebe uma linha por teste a cada execução** (`append`).
# MAGIC Ela nunca é apagada: é o histórico. O `execucao_id` junta as linhas de uma mesma rodada.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS qualidade.resultados_testes (
# MAGIC   execucao_id   STRING    COMMENT 'Identifica uma rodada: todos os testes rodados juntos',
# MAGIC   executado_em  TIMESTAMP COMMENT 'Quando a rodada aconteceu (UTC)',
# MAGIC   teste         STRING    COMMENT 'Id do teste (T01, T02...)',
# MAGIC   regra         STRING    COMMENT 'Regra do contrato que o teste prova (RN-xx)',
# MAGIC   tipo          STRING    COMMENT 'unicidade, domínio, não nulo, reconciliação, regra de negócio, regressão',
# MAGIC   tabela        STRING    COMMENT 'Tabela testada',
# MAGIC   linhas_ruins  BIGINT    COMMENT 'Quantas linhas violam a regra (0 = passou)',
# MAGIC   resultado     STRING    COMMENT 'OK ou FALHOU'
# MAGIC )
# MAGIC COMMENT 'Histórico dos testes de qualidade do Módulo 01 (aula 4). Uma linha por teste por execução.'

# COMMAND ----------

def rodar_testes(testes):
    execucao_id = str(uuid.uuid4())[:8]
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    linhas = []
    for teste_id, regra, tipo, tabela, sql in testes:
        try:
            ruins = int(um(sql))
        except Exception as e:
            print(f"{teste_id}: o SQL do teste quebrou → {type(e).__name__}: {str(e).splitlines()[0][:120]}")
            ruins = -1   # -1 = o teste nem conseguiu rodar (também é falha)
        linhas.append((execucao_id, agora, teste_id, regra, tipo, tabela, ruins, "OK" if ruins == 0 else "FALHOU"))
    (spark.createDataFrame(linhas, "execucao_id string, executado_em timestamp, teste string, regra string, "
                                   "tipo string, tabela string, linhas_ruins bigint, resultado string")
     .write.mode("append").saveAsTable("qualidade.resultados_testes"))
    return execucao_id

EXECUCAO = rodar_testes(TESTES)
display(spark.sql(f"SELECT teste, regra, tipo, tabela, linhas_ruins, resultado "
                  f"FROM qualidade.resultados_testes WHERE execucao_id = '{EXECUCAO}' ORDER BY teste"))

# COMMAND ----------

# MAGIC %md
# MAGIC Esperado: 9 linhas, todas `OK` com `linhas_ruins = 0`.
# MAGIC
# MAGIC ## Passo 4 · O histórico
# MAGIC Uma segunda rodada, como se fosse amanhã. Depois, a consulta mostra cada rodada separada, com a hora.

# COMMAND ----------

EXECUCAO = rodar_testes(TESTES)
print(f"Segunda rodada: {EXECUCAO}")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   execucao_id,
# MAGIC   MIN(executado_em)                                          AS executado_em,
# MAGIC   COUNT(*)                                                   AS testes,
# MAGIC   SUM(CASE WHEN resultado = 'OK' THEN 1 ELSE 0 END)          AS ok,
# MAGIC   SUM(CASE WHEN resultado = 'FALHOU' THEN 1 ELSE 0 END)      AS falhas
# MAGIC FROM qualidade.resultados_testes
# MAGIC GROUP BY execucao_id
# MAGIC ORDER BY executado_em DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 5 · Constraints: barrar na entrada
# MAGIC
# MAGIC O teste confere **depois** que o dado entrou. A constraint do Delta age **antes**: se uma linha nova viola a regra,
# MAGIC a escrita inteira é recusada e nada entra ([doc](https://docs.databricks.com/aws/en/tables/constraints)).
# MAGIC
# MAGIC | | Teste | Constraint |
# MAGIC |---|---|---|
# MAGIC | Quando age | depois de escrever | na hora de escrever |
# MAGIC | O que olha | qualquer coisa, até várias tabelas (reconciliação) | uma linha de cada vez, de uma tabela |
# MAGIC | Se der problema | registra e avisa | recusa a escrita |
# MAGIC
# MAGIC Os dois juntos: a constraint segura o que dá para checar linha a linha; o teste cobre o resto.
# MAGIC
# MAGIC Para poder rodar este notebook de novo, cada constraint é removida (se existir) antes de ser criada.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- RN-03: todo status atual tem pedido
# MAGIC ALTER TABLE silver.status_atual ALTER COLUMN order_id SET NOT NULL;
# MAGIC
# MAGIC -- RN-01: só os 5 status do contrato
# MAGIC ALTER TABLE silver.status_atual DROP CONSTRAINT IF EXISTS rn01_status_valido;
# MAGIC ALTER TABLE silver.status_atual ADD CONSTRAINT rn01_status_valido
# MAGIC   CHECK (status IN ('criado', 'pago', 'enviado', 'entregue', 'cancelado'));
# MAGIC
# MAGIC -- RN-05: venda é positiva e o desconto nunca aumenta o preço
# MAGIC ALTER TABLE silver.pedidos DROP CONSTRAINT IF EXISTS rn05_liquido_ate_bruto;
# MAGIC ALTER TABLE silver.pedidos ADD CONSTRAINT rn05_liquido_ate_bruto
# MAGIC   CHECK (valor_liquido > 0 AND valor_liquido <= valor_bruto);

# COMMAND ----------

# MAGIC %md
# MAGIC As constraints ficam guardadas nas propriedades da tabela:

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TBLPROPERTIES silver.status_atual

# COMMAND ----------

# MAGIC %md
# MAGIC Procure a linha `delta.constraints.rn01_status_valido`.
# MAGIC
# MAGIC ## Passo 6 · Tentando passar dado ruim
# MAGIC
# MAGIC Duas tentativas de inserir um status fora do contrato. A célula mostra o erro sem quebrar o notebook.

# COMMAND ----------

def tentar(descricao, sql):
    try:
        spark.sql(sql)
        print(f"⚠️  {descricao}: ENTROU (a constraint não segurou)")
    except Exception as e:
        msg = str(e)
        msg = msg[msg.find("["):] if "[" in msg else msg          # pula o nome interno da exceção
        msg = msg.split("JVM stacktrace")[0]                     # o resto é o rastro interno do Java
        linhas = [l.strip() for l in msg.splitlines() if l.strip()][:3]
        print(f"🛑 {descricao}: recusado\n   " + "\n   ".join(l[:240] for l in linhas))

tentar("status 'Entregue' (com maiúscula)",
       "INSERT INTO silver.status_atual VALUES (99999, 'Entregue', current_timestamp(), 'ev-teste')")
tentar("pedido sem order_id",
       "INSERT INTO silver.status_atual VALUES (NULL, 'entregue', current_timestamp(), 'ev-teste')")

print("\nLinhas de teste que entraram:", um("SELECT COUNT(*) FROM silver.status_atual WHERE event_id = 'ev-teste'"))

# COMMAND ----------

# MAGIC %md
# MAGIC Esperado: as duas recusadas, e `0` linhas de teste na tabela. A primeira mostra a regra que foi violada
# MAGIC e o valor que tentou entrar.
# MAGIC
# MAGIC ## Passo 7 · O histórico conta o que aconteceu
# MAGIC
# MAGIC Cada `ALTER TABLE` também vira uma versão no histórico da tabela:

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT version, timestamp, operation, operationParameters
# MAGIC FROM (DESCRIBE HISTORY silver.status_atual)
# MAGIC ORDER BY version DESC
# MAGIC LIMIT 5

# COMMAND ----------

# MAGIC %md
# MAGIC Procure `CHANGE COLUMN` (o `NOT NULL`) e `ADD CONSTRAINT`. Se você já rodou a aula 3 mais de uma vez, aparece também
# MAGIC `CREATE OR REPLACE TABLE AS SELECT` mais para baixo.
# MAGIC
# MAGIC **Atenção, e isso cai em prova:** o `CREATE OR REPLACE` da aula 3 **mantém o histórico** da tabela (as versões antigas
# MAGIC continuam lá), mas a tabela nova nasce com a definição do comando novo. Ou seja: **as constraints somem**.
# MAGIC Rodou a aula 3 de novo? Rode este notebook depois. O teste da aula confere se elas estão lá.
# MAGIC
# MAGIC ## Passo 8 · Vermelho de verdade
# MAGIC Se qualquer teste da última rodada falhou, o notebook termina em erro. É isso que, num job agendado,
# MAGIC faz alguém ser avisado.

# COMMAND ----------

falhas = [r["teste"] for r in spark.sql(
    f"SELECT teste FROM qualidade.resultados_testes WHERE execucao_id = '{EXECUCAO}' AND resultado = 'FALHOU'").collect()]
assert not falhas, f"Testes que falharam: {falhas}. Veja qualidade.resultados_testes."
print(f"Rodada {EXECUCAO}: {len(TESTES)} testes, todos OK")
