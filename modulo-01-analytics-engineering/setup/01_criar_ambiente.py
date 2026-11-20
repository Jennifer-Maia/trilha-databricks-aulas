# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # 01 · Criar o ambiente do módulo
# MAGIC
# MAGIC **O que esta etapa faz:** cria o catálogo do projeto, um schema por camada e o Volume onde a API vai "pousar" os arquivos.
# MAGIC
# MAGIC **Por quê:** separar por camada deixa claro, só pelo nome, se um dado é bruto (`raw`), fiel à origem (`bronze`),
# MAGIC tratado (`silver`) ou pronto para o negócio (`gold`). Governança e qualidade ficam em schemas próprios.
# MAGIC
# MAGIC | Objeto | Tipo | Para quê |
# MAGIC |---|---|---|
# MAGIC | `<catalogo>` | catálogo | a "pasta raiz" do projeto no Unity Catalog |
# MAGIC | `raw`, `bronze`, `silver`, `gold` | schemas | uma camada do medalhão cada |
# MAGIC | `governanca`, `qualidade` | schemas | tabela de acesso (aula 5) e resultados dos testes (aula 4) |
# MAGIC | `raw.landing` | volume | pasta de arquivos gerenciada pelo Unity Catalog; recebe o JSON da API como veio |
# MAGIC
# MAGIC Pode rodar quantas vezes quiser: `IF NOT EXISTS` não apaga nem recria nada.

# COMMAND ----------

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")

spark.sql(f"CREATE CATALOG IF NOT EXISTS {CAT} COMMENT 'Módulo 01 da trilha: produto de dados de vendas por região'")
for schema, comentario in {
    "raw": "Arquivos como chegaram da fonte (Volume landing)",
    "bronze": "Tabelas fiéis à origem + metadados de carga",
    "silver": "Dados tratados com as regras de negócio (RN-01 a RN-03, RN-07)",
    "gold": "Tabelas prontas para o negócio",
    "governanca": "Tabela de acesso usuário → região, perfil",
    "qualidade": "Resultados dos testes de qualidade",
}.items():
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CAT}.{schema} COMMENT '{comentario}'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CAT}.raw.landing COMMENT 'Landing: JSON bruto da API, uma pasta por carga, nunca sobrescrito'")

display(spark.sql(f"SHOW SCHEMAS IN {CAT}"))
print(f"Volume pronto: /Volumes/{CAT}/raw/landing")