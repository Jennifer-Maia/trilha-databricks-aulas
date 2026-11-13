# Contexto 02 · Dados e API

## O dataset

[`trilhajornadadatabricks/loja-ficticia-jornada`](https://huggingface.co/datasets/trilhajornadadatabricks/loja-ficticia-jornada) no Hugging Face. Dados **fictícios**, gerados com semente fixa (42): todo mundo chega nos mesmos números. Script gerador: `modulo-01-analytics-engineering/setup/gerar_dados_loja.py`.

| Tabela (`config`) | Colunas | Linhas |
|---|---|---|
| `clientes` | `customer_id`, `nome`, `email`, `telefone`, `cidade`, `uf`, `cadastrado_em` | 500 |
| `produtos` | `product_id`, `nome`, `categoria`, `preco` | 60 |
| `pedidos` | `order_id`, `customer_id`, `criado_em`, `itens` (lista), `valor_bruto`, `valor_liquido`. **Sem status** | 1.500 |
| `eventos_pedido` | `event_id`, `order_id`, `status`, `event_ts`, `canal` | 5.416 |

Ligações: `pedidos.order_id = eventos_pedido.order_id`; `pedidos.customer_id = clientes.customer_id`.

Sujeiras de propósito (tratadas nas aulas 3 e 4): status escrito de vários jeitos (`Entregue`, `ENTREGUE`, `delivered`), eventos duplicados (174), eventos sem data (12), eventos de pedido que não existe (5), clientes sem UF.

## A API

```
GET https://datasets-server.huggingface.co/rows
    ?dataset=trilhajornadadatabricks/loja-ficticia-jornada
    &config=<tabela>&split=train&offset=<n>&length=<até 100>
```

| Item | Valor |
|---|---|
| Autenticação | nenhuma (dataset público) |
| Resposta | JSON com `features` (colunas), `rows` (lista de `{row_idx, row, truncated_cells}`), `num_rows_total` |
| Máximo por chamada | 100 linhas. `length` maior → HTTP 422 |
| Limite de chamadas | por IP. **Medido** em 10/11/2026 (não documentado, pode mudar): ~40 a 55 chamadas seguidas e vem HTTP 429; libera em ~60 s |
| Carga completa | 76 chamadas (5 + 1 + 15 + 55 páginas) |
| Ordem | a API não garante ordem dos eventos |

Tratamento no lab (aula 2): 1 s de pausa entre páginas; retry com espera que dobra (2, 4, 8… s) para 429, 500, 502, 503, 504, timeout e queda de conexão; 60 s de espera no 429; erro definitivo (outros 4xx) para na hora; até 6 tentativas.

## Números de referência

| Métrica | Valor |
|---|---|
| Linhas com `status = 'entregue'` exato | 946 |
| Linhas "entregue" ignorando maiúsculas, com duplicadas | 1.060 |
| Pedidos com status atual entregue (RN-01 a RN-03 e RN-07) | **1.052** |
| Eventos duplicados / sem data / órfãos | 174 / 12 / 5 |
| Pedidos entregues de clientes sem UF | 4 |

## Plano B

Se a API estiver bloqueada ou fora do ar: `setup/02_plano_b_sem_api` lê os mesmos dados de `setup/plano_b/*.jsonl` e grava no Volume no mesmo formato da API, com manifesto `"fonte": "plano_b"`.
