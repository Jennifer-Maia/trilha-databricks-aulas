# Aula 5 · Anotações

> Minhas notas sobre o notebook da aula, passo a passo. Use junto com o notebook aberto: cada seção aqui tem o mesmo nome do passo lá.

## Em uma frase

Uma regra de acesso só protege se ela **mora na tabela**, vale para **qualquer consulta** e é **testada** com cada perfil.

```
o mesmo SELECT ─► gold.pedidos_concluidos ─► filtro de linha (RN-08) + máscara (RN-09)
                                              └─ perguntam: quem é current_user() em governanca.acesso_usuarios?
```

---

## Passo 0 · Parâmetros

O mesmo `USE CATALOG` das aulas 3 e 4. A novidade é a variável `EU`: o seu usuário de login (`current_user()`). Ele entra na tabela de acesso no Passo 2.

## Passo 1 · Documentar: comentários e tags

```sql
COMMENT ON TABLE gold.vendas_por_regiao IS 'Vendas de pedidos concluídos por região e mês ...';
ALTER TABLE gold.pedidos_concluidos ALTER COLUMN valor_venda COMMENT 'Valor com desconto, em R$ (RN-05)';
ALTER TABLE gold.pedidos_concluidos ALTER COLUMN email SET TAGS ('pii' = 'email');
```

- **Comentário:** texto livre para quem chega depois. Aparece no Catalog e no `DESCRIBE`.
- **Tag:** etiqueta `chave = valor` que dá para procurar. `pii` quer dizer dado pessoal (em inglês, *personally identifiable information*).

Com a tag, o catálogo responde "onde tem dado pessoal?":

```sql
SELECT schema_name, table_name, column_name, tag_name, tag_value
FROM information_schema.column_tags
WHERE tag_name = 'pii'
```

Esperado: `email` e `telefone` de `pedidos_concluidos`. Se você já fez os exercícios, aparecem também as colunas de `governanca.ex05_clientes`.

Comentário e tag **documentam**. Sozinhos, não escondem nada.

## Erro de propósito · A view que "esconde"

```sql
CREATE OR REPLACE VIEW gold.v_pedidos_sem_contato AS
SELECT order_id, regiao, mes, valor_venda FROM gold.pedidos_concluidos;
```

Pela view, sem e-mail e sem telefone. Mas a mesma pessoa consulta **a tabela**:

```sql
SELECT order_id, nome, email, telefone FROM gold.pedidos_concluidos LIMIT 3
```

E vê tudo. A view é uma **cortina**: esconde de quem olha por ela. Quem tem `SELECT` na tabela passa por fora. Por isso a proteção vai na tabela.

A view é apagada logo em seguida (`DROP VIEW IF EXISTS`), porque ela não é a proteção.

## Passo 2 · A tabela de acesso

| usuario | perfil | regiao |
|---|---|---|
| (você) | financeiro | |
| ana.norte@loja-ficticia.com | vendas | Norte |
| bruno.sudeste@loja-ficticia.com | vendas | Sudeste |
| carla.fin@loja-ficticia.com | financeiro | |

No mundo real, o perfil viria de **grupos** da conta (`is_account_group_member('financeiro')`). Na Free Edition dá para criar grupos, mas você testa com uma conta só, e trocar de grupo pela tela a cada perfil seria lento. Então uma tabela diz o perfil, e a função `trocar_perfil` muda **a sua linha** para testar o que cada perfil vê.

```python
trocar_perfil("vendas", "Sudeste")   # agora você é de vendas do Sudeste
trocar_perfil("financeiro")          # de volta
```

Ela usa um `MERGE`: se a sua linha existe, atualiza; se não existe, cria.

## Passo 3 · As funções da regra

Filtro e máscara são **funções SQL** guardadas no Unity Catalog.

**Filtro (RN-08):** recebe a região da linha e devolve `TRUE` (aparece) ou `FALSE` (some).

```sql
CREATE OR REPLACE FUNCTION governanca.pode_ver_regiao(regiao_da_linha STRING)
RETURNS BOOLEAN
RETURN EXISTS (
  SELECT 1 FROM governanca.acesso_usuarios a
  WHERE a.usuario = current_user()
    AND (a.perfil = 'financeiro' OR a.regiao = regiao_da_linha)
);
```

Leia assim: "existe uma linha na tabela de acesso para mim, em que eu sou do financeiro **ou** a minha região é a região desta linha?".

**Máscaras (RN-09):** recebem o valor e devolvem o que a pessoa vai ver.

| Função | Financeiro vê | Os outros veem |
|---|---|---|
| `mascarar_email` | `ana.araujo.87@exemplo.com.br` | `***@exemplo.com.br` |
| `mascarar_telefone` | `(11) 99518-9821` | `(**) *****-9821` |

## Passo 4 · Pôr a regra na tabela

```sql
ALTER TABLE gold.pedidos_concluidos SET ROW FILTER governanca.pode_ver_regiao ON (regiao);
ALTER TABLE gold.vendas_por_regiao  SET ROW FILTER governanca.pode_ver_regiao ON (regiao);
ALTER TABLE gold.pedidos_concluidos ALTER COLUMN email    SET MASK governanca.mascarar_email;
ALTER TABLE gold.pedidos_concluidos ALTER COLUMN telefone SET MASK governanca.mascarar_telefone;
```

O `ON (regiao)` diz qual coluna da linha vai para a função. A partir daqui, **toda** consulta nessas tabelas passa pela regra: notebook, editor SQL, dashboard.

## Passo 5 · O mesmo SELECT, três perfis

A mesma consulta, trocando só o seu perfil:

| perfil | regioes | pedidos | exemplo_email |
|---|---|---|---|
| financeiro | 6 | 1052 | aberto |
| vendas Sudeste | 1 | 528 | `***@exemplo.com.br` |
| vendas Norte | 1 | 89 | `***@exemplo.com.br` |

As 6 regiões do financeiro são as 5 do IBGE mais `Não informada`.

Repare: você é a **dona** da tabela e, no perfil vendas, não vê o resto. O filtro e a máscara valem para todo mundo. No fim, a célula volta você para `financeiro`, porque os testes da aula 4 precisam ver tudo.

## Passo 6 · Quem pode consultar: GRANT

Para ler uma tabela, a pessoa precisa de um privilégio em **cada nível** do nome `catálogo.schema.tabela`:

```sql
GRANT USE CATALOG ON CATALOG jornada_comercial TO `account users`;
GRANT USE SCHEMA  ON SCHEMA gold               TO `account users`;
GRANT SELECT      ON TABLE gold.vendas_por_regiao TO `account users`;
```

`account users` é o grupo de todos os usuários da conta. Quem recebeu o `SELECT` consulta a tabela, mas **continua passando pelo filtro**. O `GRANT` abre a porta; o filtro decide o que tem do outro lado.

Para tirar: `REVOKE SELECT ON TABLE gold.vendas_por_regiao FROM \`account users\``.

## Passo 7 · Governança também se testa

Os testes vão para a mesma tabela da aula 4, `qualidade.resultados_testes`, no mesmo formato: conta as linhas ruins, 0 = passou.

| Teste | Perfil usado | Pergunta |
|---|---|---|
| T10 | vendas Sudeste | aparece pedido de outra região? |
| T11 | vendas Sudeste | e no resumo por região? |
| T12 | vendas Sudeste | aparece e-mail ou telefone aberto? |
| T13 | financeiro | falta algum pedido, ou tem e-mail mascarado? |

O T13 olha o outro lado: uma regra de acesso errada pode **esconder demais**. Aí o número do financeiro fica errado sem nenhum erro vermelho.

A função usa `try` / `finally`: mesmo se um teste quebrar no meio, o seu perfil volta para `financeiro`.

## Passo 8 · Vermelho de verdade

Dois `assert`:

1. o seu perfil voltou para `financeiro`;
2. nenhum teste da rodada falhou.

Esperado: `Governança conferida (xxxxxxxx): RN-08 e RN-09 OK, e você está de volta no perfil financeiro`.

## O teste da aula (`teste/aula05_conferir_governanca`)

Confere o **comportamento**, não só se as coisas existem. São 8 testes: a tabela de acesso, as tags, os comentários, o filtro nas duas golds (como vendas Norte), a máscara, o financeiro vendo tudo e você de volta no financeiro.

Esperado: 8 linhas `OK` e `Governança conferida: todos os testes OK`.

## Exercícios: dicas antes do gabarito

| # | Se travou |
|---|---|
| 1 | Dois `ALTER TABLE ... ALTER COLUMN ... SET TAGS`, separados por `;` |
| 2 | Copie a estrutura da `governanca.mascarar_telefone` e troque só o nome da função |
| 3 | `ALTER TABLE ... ALTER COLUMN telefone SET MASK <sua função>` |
| 4 | Se o financeiro passou a ver **0** clientes, a sua função esqueceu o `a.perfil = 'financeiro' OR` |
| 5 | Linha ruim = cliente de região diferente de `Norte`. Conte essas linhas na sua tabela protegida |

No fim, rode sempre a célula **Arrumar**: ela garante que você terminou no perfil `financeiro`.
