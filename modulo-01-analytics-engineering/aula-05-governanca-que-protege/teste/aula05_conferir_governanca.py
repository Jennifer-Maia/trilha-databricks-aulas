# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 5 · Teste: a governança protege de verdade?
# MAGIC
# MAGIC Confere o **comportamento**, não só se as coisas existem: troca o seu perfil na tabela de acesso, consulta as tabelas
# MAGIC e vê o que aparece. No fim, sempre volta você para o perfil `financeiro`.
# MAGIC
# MAGIC | Teste | Pergunta | Pega qual erro |
# MAGIC |---|---|---|
# MAGIC | tabela de acesso | você está em `governanca.acesso_usuarios`? | Passo 2 não rodou |
# MAGIC | tags de PII | `email` e `telefone` têm a tag `pii`? | Passo 1 esquecido |
# MAGIC | comentários | as duas tabelas gold têm comentário? | Passo 1 esquecido |
# MAGIC | filtro (vendas) | como vendas Norte, só aparece o Norte nas duas golds? | filtro ausente ou errado |
# MAGIC | máscara (vendas) | como vendas, e-mail e telefone mascarados? | máscara ausente |
# MAGIC | financeiro vê tudo | como financeiro, 1.052 pedidos e e-mail aberto? | regra que esconde demais |
# MAGIC | voltou para financeiro | no fim, seu perfil é `financeiro`? | testes da aula 4 quebrariam |

# COMMAND ----------

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
spark.sql(f"USE CATALOG {CAT}")

def um(sql):
    return spark.sql(sql).first()[0]

def trocar_perfil(perfil, regiao=None):
    valor_regiao = f"'{regiao}'" if regiao else "CAST(NULL AS STRING)"
    spark.sql(f"""
        MERGE INTO governanca.acesso_usuarios a
        USING (SELECT current_user() AS usuario, '{perfil}' AS perfil, {valor_regiao} AS regiao) n
        ON a.usuario = n.usuario
        WHEN MATCHED THEN UPDATE SET perfil = n.perfil, regiao = n.regiao
        WHEN NOT MATCHED THEN INSERT *
    """)

def como(perfil, regiao, sql):
    try:
        trocar_perfil(perfil, regiao)
        return um(sql)
    finally:
        trocar_perfil("financeiro")

testes = [
    ("tabela de acesso", lambda: um("SELECT COUNT(*) FROM governanca.acesso_usuarios WHERE usuario = current_user()") == 1),
    ("tags de PII", lambda: um(
        "SELECT COUNT(*) FROM information_schema.column_tags WHERE schema_name = 'gold' "
        "AND table_name = 'pedidos_concluidos' AND tag_name = 'pii' AND column_name IN ('email', 'telefone')") == 2),
    ("comentários", lambda: um(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'gold' "
        "AND table_name IN ('pedidos_concluidos', 'vendas_por_regiao') AND comment IS NOT NULL") == 2),
    ("filtro (vendas Norte, detalhe)", lambda: como("vendas", "Norte",
        "SELECT COUNT(*) > 0 AND COUNT_IF(regiao <> 'Norte') = 0 FROM gold.pedidos_concluidos")),
    ("filtro (vendas Norte, resumo)", lambda: como("vendas", "Norte",
        "SELECT COUNT(*) > 0 AND COUNT_IF(regiao <> 'Norte') = 0 FROM gold.vendas_por_regiao")),
    ("máscara (vendas)", lambda: como("vendas", "Norte",
        "SELECT COUNT_IF(email NOT LIKE '***@%' OR telefone NOT LIKE '(**) *****-%') = 0 FROM gold.pedidos_concluidos")),
    ("financeiro vê tudo", lambda: como("financeiro", None,
        "SELECT COUNT(*) = 1052 AND COUNT_IF(email LIKE '***%') = 0 FROM gold.pedidos_concluidos")),
    ("voltou para financeiro", lambda: um(
        "SELECT perfil FROM governanca.acesso_usuarios WHERE usuario = current_user()") == "financeiro"),
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

trocar_perfil("financeiro")
display(spark.createDataFrame(resultados, "teste string, resultado string, detalhe string"))
assert not falhas, f"Testes que falharam: {falhas}"
print("Governança conferida: todos os testes OK")
