# Aula 4 · Anotações

> Minhas notas sobre o notebook da aula, passo a passo. Use junto com o notebook aberto: cada seção aqui tem o mesmo nome do passo lá.

## Em uma frase

Um número só merece confiança se existe um teste que **pode falhar**, que **avisa quando falha** e que **deixa registro**. E o que dá para barrar na entrada, a constraint barra.

```
camadas da aula 3 ─► testes T01–T09 (contam linhas ruins) ─► qualidade.resultados_testes (histórico)
                  └► constraints na silver (recusam dado ruim na escrita)
```

---

## Passo 0 · Parâmetros

O mesmo `USE CATALOG` da aula 3. Se aparecer `TABLE_OR_VIEW_NOT_FOUND`, rode essa célula de novo.

## Passo 1 · Um teste é uma pergunta que procura o problema

Todo teste da aula tem o mesmo formato: **conta as linhas ruins**.

```sql
-- RN-02 · unicidade
SELECT COUNT(*) - COUNT(DISTINCT event_id) AS linhas_ruins
FROM silver.eventos_pedido
```

- `0`: passou.
- Qualquer outro número: falhou, e o número já é o tamanho do problema.

Na silver dá `0`. Na bronze, a mesma pergunta dá `174`: são os duplicados que a RN-02 tirou.

| Tipo | Pergunta |
|---|---|
| unicidade | a chave aparece uma vez só? |
| domínio | o valor está na lista permitida? |
| não nulo | o campo obrigatório veio? |
| reconciliação | o total bate com a origem? |
| regra de negócio | a regra do contrato vale linha a linha? |
| regressão | o número de referência continua o mesmo? |

## Erro de propósito · O teste que sempre passa

```sql
SELECT COUNT(*) FROM gold.vendas_por_regiao WHERE regiao = NULL   -- sempre 0
```

No SQL, `NULL` quer dizer "não sei". `regiao = NULL` pergunta "a região é igual a um valor que eu não sei?". A resposta é "não sei", e o `WHERE` só deixa passar o que é **verdadeiro**. Resultado: nenhuma linha, sempre.

Para nulo, é sempre `IS NULL` ou `IS NOT NULL`.

A prova é a **sabotagem**: uma view temporária com a gold mais uma venda sem região, colocada por nós.

```
teste_errado  teste_certo
0             1
```

O teste errado continua em 0 com a linha ruim lá dentro. Antes de confiar num teste, veja ele falhar uma vez.

O mesmo cuidado vale para `NOT IN`: `status NOT IN ('criado', ...)` não pega `status` nulo. Por isso o teste de domínio tem `status IS NULL OR ...`.

## Passo 2 · Os testes do contrato

Nove testes, cada um com o número da regra que ele prova. A lista fica numa variável Python (`TESTES`), com o SQL de cada um. Para acrescentar um teste, é só acrescentar uma linha.

O T09 (regressão) compara com 1.052. Funciona porque o nosso dado é fixo (semente 42). Com dado que cresce todo dia, a regressão compara com a rodada anterior ou com uma faixa esperada.

## Passo 3 · Rodar e guardar o resultado

A tabela `qualidade.resultados_testes` é criada **uma vez** (`CREATE TABLE IF NOT EXISTS`) e recebe linhas novas a cada rodada (`append`). Ela nunca é apagada: é o histórico.

| Coluna | Para quê |
|---|---|
| `execucao_id` | junta os testes de uma mesma rodada |
| `executado_em` | quando a rodada aconteceu (UTC) |
| `teste`, `regra`, `tipo`, `tabela` | qual teste, de qual regra, de que tipo, em qual tabela |
| `linhas_ruins` | 0 = passou; `-1` = o SQL do teste nem rodou |
| `resultado` | `OK` ou `FALHOU` |

Se o SQL de um teste quebrar, ele não some: entra como `-1` e `FALHOU`. Teste que não roda também é falha.

Esperado: 9 linhas, todas `OK`.

## Passo 4 · O histórico

Uma segunda rodada, como se fosse no dia seguinte, e uma consulta que agrupa por `execucao_id`:

```
execucao_id  executado_em         testes  ok  falhas
a1b2c3d4     2026-11-18 14:02:11  9       9   0
e5f6a7b8     2026-11-18 14:01:40  9       9   0
```

(os ids e as horas vão ser outros no seu.)

## Passo 5 · Constraints: barrar na entrada

```sql
ALTER TABLE silver.status_atual ALTER COLUMN order_id SET NOT NULL;

ALTER TABLE silver.status_atual ADD CONSTRAINT rn01_status_valido
  CHECK (status IN ('criado', 'pago', 'enviado', 'entregue', 'cancelado'));

ALTER TABLE silver.pedidos ADD CONSTRAINT rn05_liquido_ate_bruto
  CHECK (valor_liquido > 0 AND valor_liquido <= valor_bruto);
```

- `SET NOT NULL`: a coluna passa a ser obrigatória.
- `CHECK (condição)`: toda linha nova precisa respeitar a condição. Se uma linha violar, **a escrita inteira** é recusada ([doc](https://docs.databricks.com/aws/en/tables/constraints)).
- A constraint só é criada se as linhas que **já estão** na tabela respeitarem a regra.
- O `DROP CONSTRAINT IF EXISTS` antes de cada `ADD` deixa o notebook rodar de novo sem erro.

As constraints `CHECK` aparecem em `SHOW TBLPROPERTIES` como `delta.constraints.<nome>`.

**Teste ou constraint?** A constraint olha uma linha de cada vez, de uma tabela. O teste olha qualquer coisa, inclusive duas tabelas ao mesmo tempo (reconciliação). Os dois juntos.

## Passo 6 · Tentando passar dado ruim

```
🛑 status 'Entregue' (com maiúscula): recusado
   [DELTA_VIOLATE_CONSTRAINT_WITH_VALUES] CHECK constraint rn01_status_valido (status IN (...)) violated by row with values:
   - status : Entregue.
🛑 pedido sem order_id: recusado
   [DELTA_NOT_NULL_CONSTRAINT_VIOLATED] NOT NULL constraint violated for column: order_id.

Linhas de teste que entraram: 0
```

O que importa é o código entre colchetes, o nome da constraint, o valor recusado e o `0` no fim.

**Atenção:** a aula 3 recria as tabelas com `CREATE OR REPLACE`, e isso **apaga as constraints** (conferido em 18/11). Rodou a aula 3 de novo? Rode este notebook depois, para elas voltarem.

## Passo 7 · O histórico conta o que aconteceu

```sql
SELECT version, timestamp, operation, operationParameters
FROM (DESCRIBE HISTORY silver.status_atual)
ORDER BY version DESC
LIMIT 5
```

Cada `ALTER TABLE` vira uma versão da tabela: `ADD CONSTRAINT` (o `CHECK`) e `CHANGE COLUMN` (o `NOT NULL`). Logo abaixo aparecem o `RESTORE` e o `UPDATE` do Passo 10 da aula 3. As tentativas recusadas do Passo 6 **não** aparecem: escrita recusada não vira versão.

**Cai em prova:** o `CREATE OR REPLACE` da aula 3 mantém o histórico (as versões antigas continuam lá) e as permissões, mas a tabela nova nasce só com o que está no comando novo. Por isso as constraints somem.

## Passo 8 · Vermelho de verdade

Um `assert` no fim: se algum teste da última rodada falhou, o notebook termina em erro. Num job agendado, é isso que faz alguém ser avisado.

## Glossário

| Termo | Em uma frase |
|---|---|
| Teste de dados | Uma pergunta que procura o problema e conta quantas linhas ruins achou |
| Sabotagem | Colocar um problema de propósito numa cópia, para ver se o teste pega |
| Reconciliação | Conferir que o total de uma tabela bate com o total da outra de onde ela veio |
| Regressão | Conferir que um número de referência não mudou sem motivo |
| Constraint | Regra guardada na tabela Delta que recusa a escrita de linhas que a violam |
| `NULL` | "Não sei": comparar com `=` nunca dá verdadeiro; use `IS NULL` |
