# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 6 · Teste: o projeto está pronto para publicar?
# MAGIC
# MAGIC Confere o que a aula 6 deixou pronto. Só lê: não roda as aulas de novo.
# MAGIC
# MAGIC | Teste | Pergunta | Pega qual erro |
# MAGIC |---|---|---|
# MAGIC | conferência existe | `qualidade.conferencia_final` tem pelo menos uma rodada? | Passo 1 não rodou |
# MAGIC | última rodada completa | a rodada mais recente conferiu as 4 aulas? | aula esquecida na lista |
# MAGIC | última rodada verde | as 4 com `OK`? | alguma aula quebrada |
# MAGIC | perfil financeiro | você está no perfil `financeiro`? | a ficha sairia filtrada |
# MAGIC | número publicado | como financeiro, a gold tem 1.052 pedidos concluídos? | número do portfólio errado |

# COMMAND ----------

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
spark.sql(f"USE CATALOG {CAT}")

def um(sql):
    return spark.sql(sql).first()[0]

ULTIMA = "SELECT execucao_id FROM qualidade.conferencia_final ORDER BY executado_em DESC LIMIT 1"

testes = [
    ("conferência existe", lambda: um("SELECT COUNT(*) FROM qualidade.conferencia_final") > 0),
    ("última rodada completa", lambda: um(
        f"SELECT COUNT(DISTINCT etapa) FROM qualidade.conferencia_final WHERE execucao_id = ({ULTIMA})") == 4),
    ("última rodada verde", lambda: um(
        f"SELECT COUNT_IF(resultado <> 'OK') FROM qualidade.conferencia_final WHERE execucao_id = ({ULTIMA})") == 0),
    ("perfil financeiro", lambda: um(
        "SELECT perfil FROM governanca.acesso_usuarios WHERE usuario = current_user()") == "financeiro"),
    ("número publicado", lambda: um("SELECT COUNT(*) FROM gold.pedidos_concluidos") == 1052),
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
print("Projeto pronto para publicar: todos os testes OK")
