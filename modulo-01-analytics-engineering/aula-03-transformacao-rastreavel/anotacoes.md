# Aula 3 · Anotações

> Minhas notas sobre o notebook da aula, passo a passo. Use junto com o notebook aberto: cada seção aqui tem o mesmo nome do passo lá.
> Os blocos de código têm um botão de copiar no canto direito (passe o mouse em cima).

## Em uma frase

Arrumar o dado em camadas, e deixar cada regra do contrato **visível no código**, com o número dela, para qualquer pessoa conseguir rastrear um número até a regra que o produziu.

```
landing (JSON cru) ─► bronze (tabela, sem regra) ─► silver (RN-07, RN-01, RN-02, RN-03, RN-06) ─► gold (RN-04, RN-05)
```

---

## Passo 0 · Parâmetros

```python
spark.sql(f"USE CATALOG {CAT}")
```

Depois dessa linha, as células SQL usam o catálogo do widget. Por isso, no SQL, basta escrever `silver.status_atual`, sem o nome do catálogo na frente.

Se a sessão reiniciar (o notebook ficou parado um tempo), rode essa célula de novo. Sem ela, o SQL procura as tabelas no catálogo errado e dá `TABLE_OR_VIEW_NOT_FOUND`.

## Passo 1 · Bronze

A bronze só transforma o JSON em tabela. **Nenhuma regra aqui.** O status bagunçado, os duplicados, os eventos sem data: tudo continua lá, de propósito. Se uma regra estiver errada, a gente corrige na silver e refaz, sem voltar na API.

O que a bronze acrescenta são três colunas de "onde veio":

| Coluna | Para quê |
|---|---|
| `_carga_id` | qual carga da aula 2 trouxe a linha |
| `_arquivo` | de qual página (arquivo JSON) ela saiu |
| `_ingerido_em` | quando entrou na bronze |

O `_metadata.file_path` é uma coluna especial que o Databricks oferece ao ler arquivos: o caminho do arquivo de onde a linha veio ([doc](https://docs.databricks.com/aws/en/ingestion/file-metadata-column)).

Esperado: `clientes` 500, `produtos` 60, `pedidos` 1.500, `eventos_pedido` 5.416.

## Passo 2 · Olhando a bagunça

```sql
SELECT status, COUNT(*) AS eventos
FROM bronze.eventos_pedido
GROUP BY status
ORDER BY eventos DESC
```

Dez grafias para cinco status. Antes de escrever qualquer regra, eu sempre olho os valores distintos da coluna. É o jeito mais barato de descobrir o que a fonte faz.

## Passo 3 · RN-07: quarentena primeiro

Dois tipos de evento não podem seguir:

- **sem data:** não dá para saber se é o mais recente;
- **de pedido que não existe** (órfão): não tem a quem pertencer.

Eles **não são apagados**. Vão para `silver.quarentena` com o motivo, e alguém pode investigar depois.

**Por que antes de tudo?** No nosso dado, o pedido 990 tem o evento `ev-003457` (`ENTREGUE`) duas vezes: uma cópia com data e outra sem. Se a deduplicação vier primeiro, ela pode ficar justo com a cópia sem data. Aí a quarentena tira o evento inteiro, o pedido 990 deixa de aparecer como entregue, e o total vira 1.051.

Quarentena primeiro: a cópia sem data sai, a outra fica, e o total é 1.052. A ordem das regras também é regra.

Esperado:
```
sem_data            12
pedido_inexistente   5
```

## Erro de propósito · A chave errada

"Sem duplicidade" soa como "um pedido por linha". Deduplicando por `order_id`:

```
linhas  entregues
1500    0
```

Sobra o **primeiro** evento de cada pedido (quase sempre `criado`). Nenhum erro na tela, só um número errado. Por isso a pergunta 3 do contrato existe: duplicado é o **mesmo evento**, e a chave é `event_id`.

## Passo 4 · RN-01 e RN-02

A normalização (RN-01) em uma expressão:

```sql
CASE lower(trim(status))
  WHEN 'delivered' THEN 'entregue'
  WHEN 'canceled'  THEN 'cancelado'
  ELSE lower(trim(status))
END AS status
```

E a deduplicação (RN-02) em uma linha:

```sql
QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY event_timestamp) = 1
```

- `ROW_NUMBER() OVER (PARTITION BY event_id ...)` numera as linhas de cada `event_id`: 1, 2, 3…
- `QUALIFY ... = 1` fica só com a primeira de cada grupo. É um `WHERE` que funciona depois da função de janela ([doc do QUALIFY](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-qry-select-qualify)).

Guardei a grafia original em `status_original`. Se alguém duvidar da RN-01, dá para conferir linha por linha.

Esperado: 5.226 eventos e 5 status. Saíram 173 duplicados. O contrato fala em 174, porque um deles (a cópia sem data do `ev-003457`) já tinha ido para a quarentena.

## Passo 5 · RN-03: status atual

Mesma ideia do `QUALIFY`, mas agora por pedido e do mais recente para o mais antigo:

```sql
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY event_timestamp DESC, event_id DESC) = 1
```

O `event_id DESC` desempata dois eventos com a mesma hora (premissa 2 do contrato).

Esperado:
```
linhas  pedidos  entregues
1500    1500     1052
```

## Passo 6 · Clientes e pedidos

Na `silver.clientes`, a UF vira maiúscula (`upper(trim(uf))`) e ganha a região do IBGE (RN-06). Cliente sem UF fica em `Não informada`: a venda continua no total e o problema fica visível.

| Região | UFs |
|---|---|
| Norte | AC, AM, AP, PA, RO, RR, TO |
| Nordeste | AL, BA, CE, MA, PB, PE, PI, RN, SE |
| Centro-Oeste | DF, GO, MS, MT |
| Sudeste | ES, MG, RJ, SP |
| Sul | PR, RS, SC |

## Passo 7 · Gold

- `gold.pedidos_concluidos`: um pedido por linha, só os com status atual `entregue` (RN-04), valor líquido (RN-05), com os dados do cliente. Na aula 5, e-mail e telefone ganham máscara.
- `gold.vendas_por_regiao`: o resumo que a Marina pediu, por região e mês, com quantidade, valor e ticket médio.

`date_trunc('MONTH', data)` leva a data para o primeiro dia do mês: é assim que se agrupa por mês sem perder o tipo data.

## Passo 8 · Os três números da aula 1

```
A · status = 'entregue' exato                  946
B · ignorando maiúsculas, com duplicados      1060
C · contrato (RN-01, RN-02, RN-03, RN-07)     1052
```

As três pessoas da aula 1 agora são três consultas. A diferença entre elas é exatamente o que o contrato decidiu.

## Passo 9 · Checkpoint

A tabela final junta cada regra, a tabela onde ela mora e o número que prova que ela foi aplicada. Tudo `OK`? Rode o `teste/aula03_conferir_camadas`. Na aula 4, esse checkpoint vira teste de verdade, salvo numa tabela.

## Glossário

| Termo | Em uma frase |
|---|---|
| Rastreabilidade | Conseguir ir do número até a regra e a linha de código que o produziram |
| Quarentena | Tabela que guarda o que não pode seguir, com o motivo, em vez de apagar |
| Função de janela | Cálculo feito "por grupo" sem juntar as linhas (ex.: `ROW_NUMBER() OVER (PARTITION BY ...)`) |
| `QUALIFY` | Filtro aplicado depois da função de janela |
| Reconciliação | Conferir que o total de uma tabela bate com o total da outra de onde ela veio |
