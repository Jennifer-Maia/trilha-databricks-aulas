# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 6 · Validar o consumo e publicar
# MAGIC
# MAGIC **O que esta etapa faz:** confere o projeto inteiro de uma vez e prepara o que vai para o portfólio.
# MAGIC
# MAGIC | Passo | O que acontece |
# MAGIC |---|---|
# MAGIC | 1 | roda o **teste de cada aula** (2 a 5), na ordem, e guarda o resultado em `qualidade.conferencia_final` |
# MAGIC | 2 | responde o **chamado #482** do jeito que a Marina vai consumir |
# MAGIC | 3 | gera a **ficha do projeto**: os números de verdade, prontos para colar no README |
# MAGIC | 4 | vermelho de verdade: se algo falhou, o notebook para |
# MAGIC
# MAGIC **Por quê:** cada aula teve o seu teste. Mas o que vai para o portfólio é o projeto **inteiro**, e um número publicado
# MAGIC precisa ser o número que quem consome vai ver. Aqui a gente prova as duas coisas antes de publicar.
# MAGIC
# MAGIC Antes: rode as aulas 2 a 5, com o mesmo catálogo. Este notebook só lê e confere: não muda nenhuma tabela das aulas.

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

def reais(valor):
    """2302177.12 → 'R$ 2.302.177,12'"""
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def trocar_perfil(perfil, regiao=None):
    """O mesmo da aula 5: muda o SEU perfil na tabela de acesso."""
    valor_regiao = f"'{regiao}'" if regiao else "CAST(NULL AS STRING)"
    spark.sql(f"""
        MERGE INTO governanca.acesso_usuarios a
        USING (SELECT current_user() AS usuario, '{perfil}' AS perfil, {valor_regiao} AS regiao) n
        ON a.usuario = n.usuario
        WHEN MATCHED THEN UPDATE SET perfil = n.perfil, regiao = n.regiao
        WHEN NOT MATCHED THEN INSERT *
    """)

trocar_perfil("financeiro")
print(f"Catálogo: {CAT} | perfil: {um('SELECT perfil FROM governanca.acesso_usuarios WHERE usuario = current_user()')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 1 · A conferência de ponta a ponta
# MAGIC
# MAGIC Cada aula tem um notebook em `teste/` que termina em `assert`: se algo estiver errado, ele quebra.
# MAGIC Aqui a gente roda os quatro, na ordem do projeto, com `dbutils.notebook.run`
# MAGIC ([doc](https://docs.databricks.com/aws/en/notebooks/notebook-workflows)): ele roda outro notebook, passa o catálogo
# MAGIC e devolve um erro se o outro notebook quebrar.

# COMMAND ----------

TESTES_DAS_AULAS = [
    ("aula 2 · landing",    "../../aula-02-ingerindo-uma-api/teste/aula02_conferir_landing"),
    ("aula 3 · camadas",    "../../aula-03-transformacao-rastreavel/teste/aula03_conferir_camadas"),
    ("aula 4 · qualidade",  "../../aula-04-testes-que-provam/teste/aula04_conferir_qualidade"),
    ("aula 5 · governança", "../../aula-05-governanca-que-protege/teste/aula05_conferir_governanca"),
]

spark.sql("""
    CREATE TABLE IF NOT EXISTS qualidade.conferencia_final (
      execucao_id  STRING    COMMENT 'Junta as 4 conferências de uma mesma rodada',
      executado_em TIMESTAMP COMMENT 'Quando a conferência rodou (UTC)',
      etapa        STRING    COMMENT 'Qual aula foi conferida',
      resultado    STRING    COMMENT 'OK ou FALHOU',
      segundos     DOUBLE    COMMENT 'Quanto tempo o teste da aula levou',
      detalhe      STRING    COMMENT 'Primeira linha do erro, se falhou'
    ) COMMENT 'Conferência de ponta a ponta do projeto (aula 6): uma linha por aula por rodada.'
""")

EXECUCAO = str(uuid.uuid4())[:8]
linhas = []
for etapa, caminho in TESTES_DAS_AULAS:
    inicio = datetime.now(timezone.utc)
    try:
        dbutils.notebook.run(caminho, 600, {"catalogo": CAT})
        resultado, detalhe = "OK", ""
    except Exception as e:
        resultado, detalhe = "FALHOU", str(e).strip().splitlines()[0][:200]
    segundos = round((datetime.now(timezone.utc) - inicio).total_seconds(), 1)
    linhas.append((EXECUCAO, inicio.replace(tzinfo=None), etapa, resultado, segundos, detalhe))
    print(f"{'✅' if resultado == 'OK' else '❌'} {etapa} ({segundos}s) {detalhe}")

trocar_perfil("financeiro")   # o teste da aula 5 troca o perfil; garantimos a volta
(spark.createDataFrame(linhas, "execucao_id string, executado_em timestamp, etapa string, resultado string, "
                               "segundos double, detalhe string")
 .write.mode("append").saveAsTable("qualidade.conferencia_final"))

display(spark.sql(f"SELECT etapa, resultado, segundos, detalhe FROM qualidade.conferencia_final "
                  f"WHERE execucao_id = '{EXECUCAO}' ORDER BY etapa"))

# COMMAND ----------

# MAGIC %md
# MAGIC Esperado: 4 linhas `OK`. Se uma falhar, o `detalhe` diz qual `assert` quebrou: volte na aula e rode o teste dela sozinho.
# MAGIC
# MAGIC ## Passo 2 · O consumo: o que a Marina recebe
# MAGIC
# MAGIC O chamado #482 pediu vendas por região, de agosto a outubro de 2026. Esta é a consulta que um dashboard ou o editor SQL
# MAGIC faria em cima da gold. Ela passa pelo filtro e pela máscara da aula 5, como qualquer consulta.

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT regiao,
# MAGIC        SUM(quantidade_pedidos)                               AS pedidos,
# MAGIC        ROUND(SUM(valor_vendas), 2)                    AS valor_vendas,
# MAGIC        ROUND(SUM(valor_vendas) / SUM(quantidade_pedidos), 2) AS ticket_medio
# MAGIC FROM gold.vendas_por_regiao
# MAGIC GROUP BY regiao
# MAGIC ORDER BY valor_vendas DESC

# COMMAND ----------

# MAGIC %md
# MAGIC Esperado (perfil financeiro): 6 linhas, o Sudeste no topo e a soma dos pedidos dando **1.052**.
# MAGIC
# MAGIC ## Erro de propósito · A ficha gerada no perfil errado
# MAGIC
# MAGIC Agora vamos montar os números do portfólio. Imagine que você terminou um exercício da aula 5 como **vendas Sudeste**
# MAGIC e esqueceu de voltar.

# COMMAND ----------

trocar_perfil("vendas", "Sudeste")   # o "esquecimento"
concluidos = um("SELECT COUNT(*) FROM gold.pedidos_concluidos")
valor      = um("SELECT ROUND(SUM(valor_venda), 2) FROM gold.pedidos_concluidos")
print(f"Pedidos concluídos: {concluidos} | Valor de vendas: {reais(valor)}")
trocar_perfil("financeiro")

# COMMAND ----------

# MAGIC %md
# MAGIC **528**. Nenhum erro, nenhuma célula vermelha. E esse número ia para o README do seu portfólio como se fosse o total.
# MAGIC
# MAGIC Com filtro de linha, **o número depende de quem consulta**. Por isso a ficha do projeto confere o perfil antes de contar,
# MAGIC e compara com a referência do contrato (1.052).
# MAGIC
# MAGIC ## Passo 3 · A ficha do projeto

# COMMAND ----------

def ficha_do_projeto():
    perfil = um("SELECT perfil FROM governanca.acesso_usuarios WHERE usuario = current_user()")
    if perfil != "financeiro":
        raise RuntimeError(f"Você está no perfil '{perfil}': a ficha sairia com números filtrados. Rode trocar_perfil('financeiro').")
    testes_ok = um("""
        SELECT COUNT_IF(resultado = 'OK') FROM qualidade.resultados_testes
        WHERE execucao_id = (SELECT execucao_id FROM qualidade.resultados_testes WHERE teste < 'T10'
                             GROUP BY execucao_id ORDER BY MAX(executado_em) DESC LIMIT 1)
    """)
    numeros = [
        ("Fonte", "API do Hugging Face, paginada, com retry e manifesto"),
        ("Clientes · produtos · pedidos · eventos",
         f"{um('SELECT COUNT(*) FROM bronze.clientes')} · {um('SELECT COUNT(*) FROM bronze.produtos')} · "
         f"{um('SELECT COUNT(*) FROM bronze.pedidos')} · {um('SELECT COUNT(*) FROM bronze.eventos_pedido')}"),
        ("Pedidos concluídos (ago–out/2026)", f"{um('SELECT COUNT(*) FROM gold.pedidos_concluidos')}"),
        ("Valor de vendas", reais(um("SELECT ROUND(SUM(valor_venda), 2) FROM gold.pedidos_concluidos"))),
        ("Regras de negócio", "9 (RN-01 a RN-09), cada uma com teste"),
        ("Testes de qualidade na última rodada", f"{testes_ok} de 9 OK"),
        ("Governança", "filtro por região (RN-08) e máscara de e-mail e telefone (RN-09)"),
    ]
    return numeros

FICHA = ficha_do_projeto()
assert dict(FICHA)["Pedidos concluídos (ago–out/2026)"] == "1052", "A ficha não bate com o contrato (1.052)."

print("| | |\n|---|---|")
for item, valor in FICHA:
    print(f"| {item} | {valor} |")

# COMMAND ----------

# MAGIC %md
# MAGIC Copie a tabela acima para o README do seu portfólio (modelo em `docs/modelo_readme_portfolio.md`).
# MAGIC Os números saíram das tabelas, não foram digitados: se você rodar de novo amanhã, a ficha mostra o que é verdade amanhã.
# MAGIC
# MAGIC ## Passo 4 · Vermelho de verdade

# COMMAND ----------

falhas = [r["etapa"] for r in spark.sql(
    f"SELECT etapa FROM qualidade.conferencia_final WHERE execucao_id = '{EXECUCAO}' AND resultado = 'FALHOU'").collect()]
assert um("SELECT perfil FROM governanca.acesso_usuarios WHERE usuario = current_user()") == "financeiro", \
    "Seu perfil não voltou para financeiro: rode trocar_perfil('financeiro')"
assert not falhas, f"Etapas que falharam: {falhas}"
print(f"Projeto conferido de ponta a ponta ({EXECUCAO}): 4 aulas OK. Pode publicar.")
