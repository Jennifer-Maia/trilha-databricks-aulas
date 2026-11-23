# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 4 · Teste: os testes e as constraints estão no lugar?
# MAGIC
# MAGIC Confere o que a aula 4 deixou pronto. Se algo falhar, o notebook termina em vermelho e diz o quê.
# MAGIC
# MAGIC | Teste | Pergunta | Pega qual erro |
# MAGIC |---|---|---|
# MAGIC | tabela de resultados | `qualidade.resultados_testes` existe e tem o formato certo? | Passo 3 não rodou |
# MAGIC | última rodada completa | a rodada mais recente tem os 9 testes (T01 a T09)? | teste esquecido |
# MAGIC | última rodada verde | todos com `linhas_ruins = 0`? | alguma regra quebrada na aula 3 |
# MAGIC | histórico | existem pelo menos 2 rodadas? | a tabela foi sobrescrita em vez de receber `append` |
# MAGIC | constraint de status | `silver.status_atual` tem a `rn01_status_valido`? | constraint esquecida ou apagada ao refazer a aula 3 |
# MAGIC | constraint de valor | `silver.pedidos` tem a `rn05_liquido_ate_bruto`? | idem |
# MAGIC | NOT NULL | `order_id` de `silver.status_atual` é obrigatório? | idem |
# MAGIC | nada passou | nenhuma linha `ev-teste` entrou em `silver.status_atual`? | constraint que não segura |

# COMMAND ----------

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
spark.sql(f"USE CATALOG {CAT}")

def um(sql):
    return spark.sql(sql).first()[0]

def propriedades(tabela):
    return {r["key"]: r["value"] for r in spark.sql(f"SHOW TBLPROPERTIES {tabela}").collect()}

# Só as rodadas da aula 4 (T01 a T09). A aula 5 grava os testes de governança (T10+) na mesma tabela.
ULTIMA = ("SELECT execucao_id FROM qualidade.resultados_testes WHERE teste < 'T10' "
          "GROUP BY execucao_id ORDER BY MAX(executado_em) DESC LIMIT 1")

testes = [
    ("tabela de resultados", lambda: set(spark.table("qualidade.resultados_testes").columns) >=
        {"execucao_id", "executado_em", "teste", "regra", "tipo", "tabela", "linhas_ruins", "resultado"}),
    ("última rodada completa", lambda: um(
        f"SELECT COUNT(DISTINCT teste) FROM qualidade.resultados_testes WHERE execucao_id = ({ULTIMA})") == 9),
    ("última rodada verde", lambda: um(
        f"SELECT COUNT(*) FROM qualidade.resultados_testes WHERE execucao_id = ({ULTIMA}) "
        f"AND (linhas_ruins <> 0 OR resultado <> 'OK')") == 0),
    ("histórico", lambda: um("SELECT COUNT(DISTINCT execucao_id) FROM qualidade.resultados_testes WHERE teste < 'T10'") >= 2),
    ("constraint de status", lambda: "delta.constraints.rn01_status_valido" in propriedades("silver.status_atual")),
    ("constraint de valor", lambda: "delta.constraints.rn05_liquido_ate_bruto" in propriedades("silver.pedidos")),
    ("NOT NULL em order_id", lambda: not spark.table("silver.status_atual").schema["order_id"].nullable),
    ("nada passou", lambda: um("SELECT COUNT(*) FROM silver.status_atual WHERE event_id = 'ev-teste'") == 0),
]

resultados, falhas = [], []
for nome, caso in testes:
    try:
        ok, detalhe = bool(caso()), ""
    except Exception as e:
        ok, detalhe = False, f"{type(e).__name__}: {str(e).splitlines()[0][:150]}"
    resultados.append((nome, "OK" if ok else "FALHOU", detalhe))
    if not ok:
        falhas.append(nome)

display(spark.createDataFrame(resultados, "teste string, resultado string, detalhe string"))
assert not falhas, f"Testes que falharam: {falhas}"
print("Qualidade conferida: todos os testes OK")
