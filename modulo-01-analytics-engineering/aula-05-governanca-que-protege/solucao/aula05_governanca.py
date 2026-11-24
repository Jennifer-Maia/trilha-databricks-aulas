# Databricks notebook source
# MAGIC %md
# MAGIC # Aula 5 · Governança que protege de verdade
# MAGIC
# MAGIC **O que esta etapa faz:** aplica as duas últimas regras do [contrato](../../docs/contrato_de_dados.md):
# MAGIC
# MAGIC | Regra | O que diz | Como |
# MAGIC |---|---|---|
# MAGIC | RN-08 | quem é de vendas só vê a própria região | **filtro de linha** (row filter) nas tabelas gold |
# MAGIC | RN-09 | e-mail e telefone só aparecem para o financeiro | **máscara de coluna** (column mask) em `gold.pedidos_concluidos` |
# MAGIC
# MAGIC Quem é de qual perfil está numa **tabela de acesso** (`governanca.acesso_usuarios`), como a pergunta 10 do contrato decidiu.
# MAGIC Antes disso, a gente documenta as tabelas (comentários e tags) e vê por que **uma view não protege nada sozinha**.
# MAGIC
# MAGIC **Por quê:** governança que só existe num documento não protege. Aqui a regra mora na própria tabela,
# MAGIC vale para qualquer consulta (notebook, SQL, dashboard) e é **testada** por perfil, como as regras da aula 4.
# MAGIC
# MAGIC Antes: rode as aulas 3 e 4, com o mesmo catálogo.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 0 · Parâmetros

# COMMAND ----------

dbutils.widgets.text("catalogo", "jornada_comercial")
CAT = dbutils.widgets.get("catalogo")
spark.sql(f"USE CATALOG {CAT}")

def um(sql):
    return spark.sql(sql).first()[0]

EU = um("SELECT current_user()")
print(f"Catálogo: {CAT} | Você é: {EU}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 1 · Documentar: comentários e tags
# MAGIC
# MAGIC Antes de proteger, dizer o que é cada coisa. O **comentário** explica a tabela e a coluna para quem chega depois.
# MAGIC A **tag** é uma etiqueta `chave = valor` que dá para procurar: aqui, marcamos as colunas com dado pessoal (`pii`).

# COMMAND ----------

# MAGIC %sql
# MAGIC COMMENT ON TABLE gold.vendas_por_regiao IS
# MAGIC   'Vendas de pedidos concluídos por região e mês (chamado #482). Regras RN-04 a RN-06. Filtro por região: RN-08.';
# MAGIC COMMENT ON TABLE gold.pedidos_concluidos IS
# MAGIC   'Um pedido concluído por linha, com dados do cliente. E-mail e telefone mascarados fora do financeiro (RN-09).';
# MAGIC
# MAGIC ALTER TABLE gold.pedidos_concluidos ALTER COLUMN valor_venda COMMENT 'Valor com desconto, em R$ (RN-05)';
# MAGIC ALTER TABLE gold.pedidos_concluidos ALTER COLUMN regiao      COMMENT 'Região do IBGE pela UF do cliente (RN-06)';
# MAGIC
# MAGIC ALTER TABLE gold.pedidos_concluidos SET TAGS ('dominio' = 'comercial', 'camada' = 'gold');
# MAGIC ALTER TABLE gold.pedidos_concluidos ALTER COLUMN email    SET TAGS ('pii' = 'email');
# MAGIC ALTER TABLE gold.pedidos_concluidos ALTER COLUMN telefone SET TAGS ('pii' = 'telefone');

# COMMAND ----------

# MAGIC %md
# MAGIC Com a tag, dá para perguntar ao catálogo: **onde tem dado pessoal?**

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT schema_name, table_name, column_name, tag_name, tag_value
# MAGIC FROM information_schema.column_tags
# MAGIC WHERE tag_name = 'pii'
# MAGIC ORDER BY table_name, column_name

# COMMAND ----------

# MAGIC %md
# MAGIC Esperado: `email` e `telefone` de `pedidos_concluidos`.
# MAGIC
# MAGIC ## Erro de propósito · A view que "esconde"
# MAGIC
# MAGIC Um jeito comum de "proteger" e-mail e telefone: criar uma view sem essas colunas e mandar todo mundo usar a view.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW gold.v_pedidos_sem_contato AS
# MAGIC SELECT order_id, regiao, mes, valor_venda
# MAGIC FROM gold.pedidos_concluidos;
# MAGIC
# MAGIC SELECT * FROM gold.v_pedidos_sem_contato LIMIT 3

# COMMAND ----------

# MAGIC %md
# MAGIC Sem e-mail, sem telefone. Protegido? Agora a mesma pessoa consulta **a tabela**:

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT order_id, nome, email, telefone FROM gold.pedidos_concluidos LIMIT 3

# COMMAND ----------

# MAGIC %md
# MAGIC Tudo aberto. A view é uma **cortina**: esconde de quem olha por ela, mas a tabela continua lá, e qualquer pessoa com
# MAGIC `SELECT` na tabela lê tudo. Por isso a proteção vai **na tabela**: o filtro e a máscara valem para qualquer consulta.
# MAGIC
# MAGIC (A view pode continuar existindo, para facilitar a vida de quem consulta. Ela só não é a proteção.)

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP VIEW IF EXISTS gold.v_pedidos_sem_contato

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 2 · A tabela de acesso
# MAGIC
# MAGIC No mundo real, o perfil viria de **grupos** (por exemplo, `is_account_group_member('financeiro')`).
# MAGIC Na Free Edition dá para criar grupos, mas aqui testamos com uma conta só: seria preciso entrar e sair de grupo pela tela
# MAGIC a cada perfil. Por isso o contrato decidiu: uma tabela diz quem é de qual perfil, e trocar de perfil é um comando. A regra é a mesma; muda só de onde vem a resposta.
# MAGIC
# MAGIC Os usuários `@loja-ficticia.com` são inventados. A linha com **o seu usuário** é a que vamos trocar para testar.

# COMMAND ----------

spark.sql("""
    CREATE OR REPLACE TABLE governanca.acesso_usuarios (
      usuario STRING COMMENT 'E-mail de login (current_user())',
      perfil  STRING COMMENT 'financeiro: vê tudo · vendas: só a própria região, contato mascarado',
      regiao  STRING COMMENT 'Região do IBGE (só para o perfil vendas)'
    ) COMMENT 'Quem é de qual perfil (pergunta 10 do contrato). Usada pelo filtro de linha e pela máscara.'
""")
spark.sql(f"""
    INSERT INTO governanca.acesso_usuarios VALUES
      ('{EU}',                            'financeiro', NULL),
      ('ana.norte@loja-ficticia.com',     'vendas',     'Norte'),
      ('bruno.sudeste@loja-ficticia.com', 'vendas',     'Sudeste'),
      ('carla.fin@loja-ficticia.com',     'financeiro', NULL)
""")

def trocar_perfil(perfil, regiao=None):
    """Muda o SEU perfil na tabela de acesso. É assim que a gente testa o que cada perfil vê."""
    valor_regiao = f"'{regiao}'" if regiao else "CAST(NULL AS STRING)"
    spark.sql(f"""
        MERGE INTO governanca.acesso_usuarios a
        USING (SELECT current_user() AS usuario, '{perfil}' AS perfil, {valor_regiao} AS regiao) n
        ON a.usuario = n.usuario
        WHEN MATCHED THEN UPDATE SET perfil = n.perfil, regiao = n.regiao
        WHEN NOT MATCHED THEN INSERT *
    """)

display(spark.table("governanca.acesso_usuarios"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 3 · As funções da regra
# MAGIC
# MAGIC Filtro de linha e máscara são **funções SQL** guardadas no Unity Catalog
# MAGIC ([doc](https://docs.databricks.com/aws/en/tables/row-and-column-filters)):
# MAGIC
# MAGIC - o **filtro** recebe o valor de uma coluna da linha e devolve `TRUE` (a linha aparece) ou `FALSE` (some);
# MAGIC - a **máscara** recebe o valor da coluna e devolve o que a pessoa vai ver.
# MAGIC
# MAGIC As duas olham `current_user()`, quem está consultando agora, na tabela de acesso.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- RN-08: vendas só vê a própria região; financeiro vê tudo
# MAGIC CREATE OR REPLACE FUNCTION governanca.pode_ver_regiao(regiao_da_linha STRING)
# MAGIC RETURNS BOOLEAN
# MAGIC COMMENT 'Filtro de linha da RN-08. Consulta governanca.acesso_usuarios.'
# MAGIC RETURN EXISTS (
# MAGIC   SELECT 1 FROM governanca.acesso_usuarios a
# MAGIC   WHERE a.usuario = current_user()
# MAGIC     AND (a.perfil = 'financeiro' OR a.regiao = regiao_da_linha)
# MAGIC );
# MAGIC
# MAGIC -- RN-09: e-mail aberto só para o financeiro
# MAGIC CREATE OR REPLACE FUNCTION governanca.mascarar_email(email STRING)
# MAGIC RETURNS STRING
# MAGIC COMMENT 'Máscara da RN-09: troca o nome antes do @ por ***.'
# MAGIC RETURN CASE
# MAGIC   WHEN EXISTS (SELECT 1 FROM governanca.acesso_usuarios a
# MAGIC                WHERE a.usuario = current_user() AND a.perfil = 'financeiro') THEN email
# MAGIC   ELSE regexp_replace(email, '^[^@]+', '***')
# MAGIC END;
# MAGIC
# MAGIC -- RN-09: telefone aberto só para o financeiro
# MAGIC CREATE OR REPLACE FUNCTION governanca.mascarar_telefone(telefone STRING)
# MAGIC RETURNS STRING
# MAGIC COMMENT 'Máscara da RN-09: mostra só os 4 últimos dígitos.'
# MAGIC RETURN CASE
# MAGIC   WHEN EXISTS (SELECT 1 FROM governanca.acesso_usuarios a
# MAGIC                WHERE a.usuario = current_user() AND a.perfil = 'financeiro') THEN telefone
# MAGIC   ELSE concat('(**) *****-', right(telefone, 4))
# MAGIC END;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 4 · Pôr a regra na tabela

# COMMAND ----------

# MAGIC %sql
# MAGIC ALTER TABLE gold.pedidos_concluidos SET ROW FILTER governanca.pode_ver_regiao ON (regiao);
# MAGIC ALTER TABLE gold.vendas_por_regiao  SET ROW FILTER governanca.pode_ver_regiao ON (regiao);
# MAGIC
# MAGIC ALTER TABLE gold.pedidos_concluidos ALTER COLUMN email    SET MASK governanca.mascarar_email;
# MAGIC ALTER TABLE gold.pedidos_concluidos ALTER COLUMN telefone SET MASK governanca.mascarar_telefone;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Passo 5 · O mesmo SELECT, três perfis
# MAGIC
# MAGIC Agora o teste que importa: **a mesma consulta**, trocando só o seu perfil na tabela de acesso.

# COMMAND ----------

CONSULTA = """
    SELECT COUNT(DISTINCT regiao) AS regioes,
           COUNT(*)               AS pedidos,
           MIN(email)             AS exemplo_email,
           MIN(telefone)          AS exemplo_telefone
    FROM gold.pedidos_concluidos
"""
linhas = []
for perfil, regiao in [("financeiro", None), ("vendas", "Sudeste"), ("vendas", "Norte")]:
    trocar_perfil(perfil, regiao)
    r = spark.sql(CONSULTA).first()
    linhas.append((f"{perfil} {regiao or ''}".strip(), r["regioes"], r["pedidos"], r["exemplo_email"], r["exemplo_telefone"]))
trocar_perfil("financeiro")   # sempre voltar para financeiro (os testes da aula 4 precisam ver tudo)

display(spark.createDataFrame(linhas, "perfil string, regioes long, pedidos long, exemplo_email string, exemplo_telefone string"))

# COMMAND ----------

# MAGIC %md
# MAGIC Esperado:
# MAGIC
# MAGIC | perfil | regiões | pedidos | e-mail |
# MAGIC |---|---|---|---|
# MAGIC | financeiro | 6 | 1052 | aberto |
# MAGIC | vendas Sudeste | 1 | só os do Sudeste | `***@...` |
# MAGIC | vendas Norte | 1 | só os do Norte | `***@...` |
# MAGIC
# MAGIC Repare que **você é a dona da tabela** e mesmo assim, no perfil vendas, não vê o resto. O filtro e a máscara valem para todo mundo.
# MAGIC
# MAGIC ## Passo 6 · Quem pode consultar: GRANT
# MAGIC
# MAGIC Filtro e máscara decidem **o que** aparece. O `GRANT` decide **quem pode consultar**. Para ler uma tabela, a pessoa
# MAGIC precisa de três permissões, uma em cada nível do nome `catálogo.schema.tabela`
# MAGIC ([doc](https://docs.databricks.com/aws/en/data-governance/unity-catalog/manage-privileges/)):

# COMMAND ----------

spark.sql(f"GRANT USE CATALOG ON CATALOG {CAT} TO `account users`")
spark.sql("GRANT USE SCHEMA ON SCHEMA gold TO `account users`")
spark.sql("GRANT SELECT ON TABLE gold.vendas_por_regiao TO `account users`")
display(spark.sql("SHOW GRANTS ON TABLE gold.vendas_por_regiao"))

# COMMAND ----------

# MAGIC %md
# MAGIC `account users` é o grupo de todos os usuários da conta. Quem recebeu o `SELECT` consulta a tabela, mas **continua passando pelo filtro**:
# MAGIC o `GRANT` abre a porta, o filtro decide o que tem do outro lado.
# MAGIC
# MAGIC Para tirar: `REVOKE SELECT ON TABLE gold.vendas_por_regiao FROM \`account users\``.
# MAGIC
# MAGIC ## Passo 7 · Governança também se testa
# MAGIC
# MAGIC Os testes da RN-08 e da RN-09 vão para a mesma tabela da aula 4, `qualidade.resultados_testes`, com o mesmo formato:
# MAGIC um número de linhas ruins, 0 = passou.

# COMMAND ----------

import uuid
from datetime import datetime, timezone

def testes_de_governanca():
    resultados = []
    try:
        trocar_perfil("vendas", "Sudeste")
        fora_da_regiao = um("SELECT COUNT(*) FROM gold.pedidos_concluidos WHERE regiao <> 'Sudeste'")
        resumo_fora    = um("SELECT COUNT(*) FROM gold.vendas_por_regiao WHERE regiao <> 'Sudeste'")
        email_aberto   = um("SELECT COUNT(*) FROM gold.pedidos_concluidos WHERE email NOT LIKE '***@%'")
        fone_aberto    = um("SELECT COUNT(*) FROM gold.pedidos_concluidos WHERE telefone NOT LIKE '(**) *****-%'")
        trocar_perfil("financeiro")
        financeiro_incompleto = abs(um("SELECT COUNT(*) FROM gold.pedidos_concluidos") - 1052)
        email_mascarado_fin   = um("SELECT COUNT(*) FROM gold.pedidos_concluidos WHERE email LIKE '***%'")
    finally:
        trocar_perfil("financeiro")
    resultados += [
        ("T10", "RN-08", "governança", "gold.pedidos_concluidos", fora_da_regiao),
        ("T11", "RN-08", "governança", "gold.vendas_por_regiao", resumo_fora),
        ("T12", "RN-09", "governança", "gold.pedidos_concluidos", email_aberto + fone_aberto),
        ("T13", "RN-08", "governança", "gold.pedidos_concluidos", financeiro_incompleto + email_mascarado_fin),
    ]
    execucao_id, agora = str(uuid.uuid4())[:8], datetime.now(timezone.utc).replace(tzinfo=None)
    linhas = [(execucao_id, agora, t, rn, tipo, tab, int(ruins), "OK" if ruins == 0 else "FALHOU")
              for t, rn, tipo, tab, ruins in resultados]
    (spark.createDataFrame(linhas, "execucao_id string, executado_em timestamp, teste string, regra string, "
                                   "tipo string, tabela string, linhas_ruins bigint, resultado string")
     .write.mode("append").saveAsTable("qualidade.resultados_testes"))
    return execucao_id

EXECUCAO = testes_de_governanca()
display(spark.sql(f"SELECT teste, regra, tabela, linhas_ruins, resultado FROM qualidade.resultados_testes "
                  f"WHERE execucao_id = '{EXECUCAO}' ORDER BY teste"))

# COMMAND ----------

# MAGIC %md
# MAGIC | Teste | Pergunta |
# MAGIC |---|---|
# MAGIC | T10 | como vendas Sudeste, aparece pedido de outra região? |
# MAGIC | T11 | e no resumo por região? |
# MAGIC | T12 | como vendas, aparece e-mail ou telefone aberto? |
# MAGIC | T13 | como financeiro, falta algum pedido ou tem e-mail mascarado? (a proteção não pode esconder demais) |
# MAGIC
# MAGIC Esperado: 4 linhas `OK`. O T13 é importante: uma regra de acesso errada pode **esconder demais**, e aí o número do financeiro fica errado sem ninguém perceber.
# MAGIC
# MAGIC ## Passo 8 · Vermelho de verdade

# COMMAND ----------

falhas = [r["teste"] for r in spark.sql(
    f"SELECT teste FROM qualidade.resultados_testes WHERE execucao_id = '{EXECUCAO}' AND resultado = 'FALHOU'").collect()]
assert um("SELECT perfil FROM governanca.acesso_usuarios WHERE usuario = current_user()") == "financeiro", \
    "Seu perfil não voltou para financeiro: rode trocar_perfil('financeiro')"
assert not falhas, f"Testes de governança que falharam: {falhas}"
print(f"Governança conferida ({EXECUCAO}): RN-08 e RN-09 OK, e você está de volta no perfil financeiro")
