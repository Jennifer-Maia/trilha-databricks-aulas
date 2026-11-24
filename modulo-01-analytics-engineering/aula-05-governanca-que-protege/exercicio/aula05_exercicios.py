# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 5 · Exercícios: proteja uma tabela e prove que protegeu
# MAGIC
# MAGIC Você vai proteger uma cópia de `silver.clientes` só sua, a `governanca.ex05_clientes`, com as mesmas regras da aula:
# MAGIC
# MAGIC | # | Exercício | Regra |
# MAGIC |---|---|---|
# MAGIC | 1 | Marcar as colunas de dado pessoal com a tag `pii` | documentação |
# MAGIC | 2 | Função de máscara para o telefone | RN-09 |
# MAGIC | 3 | Pôr a máscara na coluna | RN-09 |
# MAGIC | 4 | Função de filtro e filtro na tabela | RN-08 |
# MAGIC | 5 | Um teste que prova o filtro (e falha sem ele) | RN-08 |
# MAGIC
# MAGIC **Como funciona:** escreva o comando SQL dentro das aspas triplas onde estiver `✏️` e rode a célula. Depois rode **Conferir**.
# MAGIC As conferências trocam o seu perfil na tabela de acesso para testar e **sempre voltam você para `financeiro`** no fim.
# MAGIC
# MAGIC Antes: rode a aula 5 (a tabela `governanca.acesso_usuarios` precisa existir). O gabarito está em `solucao/aula05_exercicios_gabarito`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Preparação (só rodar)

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
    """Roda o SQL com o seu perfil trocado e volta para financeiro, mesmo se der erro."""
    try:
        trocar_perfil(perfil, regiao)
        return um(sql)
    finally:
        trocar_perfil("financeiro")

def pendente(sql):
    return not sql.strip() or "✏️" in sql

def aplicar(exercicio, sql):
    if pendente(sql):
        print(f"⏳ {exercicio}: escreva o comando e rode de novo.")
        return
    for comando in [c for c in sql.split(";") if c.strip()]:
        spark.sql(comando)
    print(f"{exercicio}: comando aplicado. Agora rode a célula Conferir.")

def conferir(exercicio, sql, casos):
    if pendente(sql):
        print(f"⏳ {exercicio}: ainda falta escrever o comando.")
        return
    tudo_certo = True
    for descricao, caso in casos:
        try:
            passou, detalhe = bool(caso()), ""
        except Exception as e:
            passou, detalhe = False, f"  →  {type(e).__name__}: {str(e).splitlines()[0][:160]}"
        print(("✅ " if passou else "❌ ") + descricao + detalhe)
        tudo_certo = tudo_certo and passou
    trocar_perfil("financeiro")
    print(f"\n🎉 {exercicio}: tudo certo!" if tudo_certo else f"\n{exercicio}: ainda não. Releia a dica e tente de novo.")

trocar_perfil("financeiro")
spark.sql("CREATE OR REPLACE TABLE governanca.ex05_clientes AS SELECT customer_id, nome, email, telefone, uf, regiao FROM silver.clientes")
CLIENTES_NORTE = um("SELECT COUNT(*) FROM governanca.ex05_clientes WHERE regiao = 'Norte'")
print(f"governanca.ex05_clientes pronta: {um('SELECT COUNT(*) FROM governanca.ex05_clientes')} clientes, {CLIENTES_NORTE} no Norte")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 1 · Marcar o dado pessoal
# MAGIC
# MAGIC Ponha a tag `pii` nas colunas `email` (valor `'email'`) e `telefone` (valor `'telefone'`) de `governanca.ex05_clientes`.
# MAGIC Dois comandos, separados por `;`.
# MAGIC
# MAGIC **Dica:** `ALTER TABLE <tabela> ALTER COLUMN <coluna> SET TAGS ('chave' = 'valor')`.

# COMMAND ----------

sql_ex1 = """
-- ✏️ Exercício 1: escreva os dois ALTER TABLE aqui
"""
aplicar("Exercício 1", sql_ex1)

# COMMAND ----------

conferir("Exercício 1", sql_ex1, [
    ("email tem a tag pii = 'email'", lambda: um(
        "SELECT COUNT(*) FROM information_schema.column_tags WHERE schema_name = 'governanca' AND table_name = 'ex05_clientes' "
        "AND column_name = 'email' AND tag_name = 'pii' AND tag_value = 'email'") == 1),
    ("telefone tem a tag pii = 'telefone'", lambda: um(
        "SELECT COUNT(*) FROM information_schema.column_tags WHERE schema_name = 'governanca' AND table_name = 'ex05_clientes' "
        "AND column_name = 'telefone' AND tag_name = 'pii' AND tag_value = 'telefone'") == 1),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 2 · A máscara do telefone
# MAGIC
# MAGIC Crie a função `governanca.ex05_mascarar_telefone(telefone STRING)` que devolve:
# MAGIC
# MAGIC - o telefone **inteiro**, se você é do perfil `financeiro` na tabela `governanca.acesso_usuarios`;
# MAGIC - senão, `'(**) *****-'` seguido dos **4 últimos** caracteres do telefone.
# MAGIC
# MAGIC **Dica:** copie a estrutura da `governanca.mascarar_telefone` da aula: `CASE WHEN EXISTS (SELECT 1 FROM ... WHERE usuario = current_user() AND perfil = 'financeiro') THEN ... ELSE ... END`.

# COMMAND ----------

sql_ex2 = """
-- ✏️ Exercício 2: escreva o CREATE OR REPLACE FUNCTION aqui
"""
aplicar("Exercício 2", sql_ex2)

# COMMAND ----------

conferir("Exercício 2", sql_ex2, [
    ("financeiro vê o telefone inteiro", lambda: como("financeiro", None,
        "SELECT governanca.ex05_mascarar_telefone('(11) 91234-5678')") == "(11) 91234-5678"),
    ("vendas vê só os 4 últimos dígitos", lambda: como("vendas", "Norte",
        "SELECT governanca.ex05_mascarar_telefone('(11) 91234-5678')") == "(**) *****-5678"),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 3 · Pôr a máscara na coluna
# MAGIC
# MAGIC Aplique a sua função na coluna `telefone` de `governanca.ex05_clientes`.
# MAGIC
# MAGIC **Dica:** `ALTER TABLE <tabela> ALTER COLUMN <coluna> SET MASK <função>`.

# COMMAND ----------

sql_ex3 = """
-- ✏️ Exercício 3: escreva o ALTER TABLE aqui
"""
aplicar("Exercício 3", sql_ex3)

# COMMAND ----------

conferir("Exercício 3", sql_ex3, [
    ("como vendas, nenhum telefone aberto na tabela", lambda: como("vendas", "Norte",
        "SELECT COUNT_IF(telefone NOT LIKE '(**) *****-%') FROM governanca.ex05_clientes") == 0),
    ("como financeiro, todos os telefones abertos", lambda: como("financeiro", None,
        "SELECT COUNT_IF(telefone LIKE '(**)%') FROM governanca.ex05_clientes") == 0),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 4 · O filtro de região
# MAGIC
# MAGIC Crie a função `governanca.ex05_pode_ver(regiao_da_linha STRING)`, que devolve `TRUE` se você é `financeiro`
# MAGIC **ou** se a sua região na tabela de acesso é igual à região da linha. Depois aplique como filtro de linha em
# MAGIC `governanca.ex05_clientes`, na coluna `regiao`. Dois comandos, separados por `;`.
# MAGIC
# MAGIC **Dica:** `RETURN EXISTS (SELECT 1 FROM governanca.acesso_usuarios a WHERE ...)` e
# MAGIC `ALTER TABLE <tabela> SET ROW FILTER <função> ON (<coluna>)`.

# COMMAND ----------

sql_ex4 = """
-- ✏️ Exercício 4: escreva o CREATE OR REPLACE FUNCTION e o ALTER TABLE aqui
"""
aplicar("Exercício 4", sql_ex4)

# COMMAND ----------

conferir("Exercício 4", sql_ex4, [
    (f"como vendas Norte, aparecem só os {CLIENTES_NORTE} clientes do Norte", lambda: como("vendas", "Norte",
        "SELECT COUNT(*) FROM governanca.ex05_clientes") == CLIENTES_NORTE),
    ("como vendas Norte, nenhuma outra região", lambda: como("vendas", "Norte",
        "SELECT COUNT_IF(regiao <> 'Norte') FROM governanca.ex05_clientes") == 0),
    ("como financeiro, os 500 clientes", lambda: como("financeiro", None,
        "SELECT COUNT(*) FROM governanca.ex05_clientes") == 500),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exercício 5 · Um teste que prova o filtro
# MAGIC
# MAGIC Como na aula 4: escreva um `SELECT` que **conta as linhas ruins**. Aqui, linha ruim é um cliente de **outra região**
# MAGIC que aparece para quem é de vendas do **Norte**, lendo `governanca.ex05_clientes`.
# MAGIC
# MAGIC A conferência roda o seu teste como vendas Norte duas vezes: na sua tabela protegida (tem que dar 0) e em `silver.clientes`,
# MAGIC que **não tem filtro** (tem que dar mais que 0). Se der 0 nas duas, o seu teste não enxerga o problema.

# COMMAND ----------

teste_ex5 = """
-- ✏️ Exercício 5: escreva o SELECT aqui (use governanca.ex05_clientes)
"""

# COMMAND ----------

conferir("Exercício 5", teste_ex5, [
    ("na tabela protegida deu 0 (o filtro funciona)", lambda: como("vendas", "Norte", teste_ex5) == 0),
    ("usa a tabela pedida", lambda: "governanca.ex05_clientes" in teste_ex5),
    ("sem o filtro (silver.clientes) deu mais que 0 (o teste pega)", lambda: como("vendas", "Norte",
        teste_ex5.replace("governanca.ex05_clientes", "silver.clientes")) > 0),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Arrumar (rode sempre no fim)
# MAGIC Garante que você terminou no perfil `financeiro`. Os testes das aulas 4 e 5 precisam disso.

# COMMAND ----------

trocar_perfil("financeiro")
print("Perfil:", um("SELECT perfil FROM governanca.acesso_usuarios WHERE usuario = current_user()"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Desafios extras (sem gabarito)
# MAGIC
# MAGIC 1. Mude a máscara do e-mail para mostrar a **primeira letra** do nome: `d***@exemplo.com.br`.
# MAGIC 2. Crie um perfil `diretoria` que vê **todas** as regiões, mas com e-mail e telefone mascarados.
# MAGIC 3. Rode a aula 3 de novo e depois o teste da aula 5. O filtro e a máscara continuam lá? Por quê?
