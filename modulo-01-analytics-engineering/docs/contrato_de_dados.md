# Contrato de dados · Vendas por região (v0.2)

> Documento apresentado na aula 1 (slides `slides/aula-01.html`). Esta versão é o gabarito.
> Tudo marcado como **Premissa** foi assumido por nós e precisa ser confirmado pela área de negócio.

## 1. O pedido original (chamado fictício do projeto)

> **Chamado #482 · Solicitação de dados** · Prioridade alta · Prazo: reunião de segunda
> **Solicitante:** Marina, Gerente Comercial
>
> Preciso ver as **vendas** por **região**, considerando só pedidos **concluídos** e **sem duplicidade**, porque o número do último relatório não bateu com o financeiro.
> O time de vendas de cada região só pode ver a **própria região**. E ninguém fora do **financeiro** pode ver e-mail e telefone de cliente.

## 2. Perguntas antes de codar

| # | Palavra ambígua | Pergunta para a Marina | Resposta / Premissa |
|---|---|---|---|
| 1 | “concluído” | Concluído é pago, enviado ou entregue? | **Premissa:** status atual = `entregue` |
| 2 | “status atual” | Se o pedido tem vários eventos, qual vale? | **Premissa:** o evento mais recente por `event_ts`; empate → maior `event_id` |
| 3 | “duplicidade” | Duplicado é o mesmo pedido ou o mesmo evento repetido? | **Premissa:** mesmo `event_id` = mesmo evento; contar uma vez |
| 4 | “vendas” | Valor bruto ou com desconto? | **Premissa:** com desconto (`valor_liquido`), em R$ |
| 5 | “região” | Região de quê: do cliente ou da entrega? Qual divisão? | **Premissa:** UF do cliente agrupada nas 5 regiões do IBGE (Norte, Nordeste, Centro-Oeste, Sudeste, Sul) |
| 6 | período | Qual período e qual data conta? | **Premissa:** data do evento de entrega, ago–out/2026 |
| 7 | cancelado | Pedido entregue e depois cancelado conta? | **Premissa:** vale o status mais recente; se for `cancelado`, não conta |
| 8 | sem data | Evento sem data entra? | **Premissa:** não entra no cálculo; vai para a quarentena |
| 9 | órfão / sem UF | Evento de pedido que não existe? Cliente sem UF? | **Premissa:** evento órfão vai para a quarentena; cliente sem UF entra como região `Não informada` e é reportado |
| 10 | “financeiro” | Quem exatamente é o financeiro? | **Premissa:** uma tabela de acesso (`usuario → regiao, perfil`) define quem é `financeiro`; os demais veem e-mail e telefone mascarados |

## 3. Fonte: API do serviço de dados da loja

A loja publica seus dados num serviço com API REST pública (Hugging Face datasets-server).

| Tabela (config) | O que traz | Linhas |
|---|---|---|
| `pedidos` | `order_id`, `customer_id`, `criado_em`, `itens` (lista de produtos), `valor_bruto`, `valor_liquido`. **Sem status.** | 1.500 |
| `eventos_pedido` | Mudanças de status: `event_id`, `order_id`, `status`, `event_ts`, `canal` | 5.416 |
| `clientes` | `customer_id`, `nome`, `email`, `telefone`, `cidade`, `uf` | 500 |
| `produtos` | `product_id`, `nome`, `categoria`, `preco` | 60 |

Como a API funciona: `GET /rows?dataset=trilhajornadadatabricks/loja-ficticia-jornada&config=<tabela>&split=train&offset=<n>&length=<até 100>`. A resposta traz `num_rows_total`. A API **não garante ordem** dos eventos.

Ligações: `pedidos.order_id = eventos_pedido.order_id` e `pedidos.customer_id = clientes.customer_id`.

## 4. Regras de negócio

| ID | Regra | Onde será implementada (aula 3) | Como será testada (aula 4) |
|---|---|---|---|
| RN-01 | Status normalizado: `Entregue`, `ENTREGUE`, `delivered` → `entregue`; `Cancelado`, `CANCELED` → `cancelado` | silver | teste de domínio: só 5 status válidos |
| RN-02 | Evento duplicado (mesmo `event_id`) conta uma vez | silver | teste de unicidade de `event_id` |
| RN-03 | Status atual = evento mais recente por pedido | silver | teste: 1 linha por `order_id` |
| RN-04 | Pedido concluído = status atual `entregue` | gold | teste de regra de negócio |
| RN-05 | Valor da venda = `valor_liquido` | gold | reconciliação: soma da gold = soma dos pedidos concluídos na silver |
| RN-06 | Região = UF do cliente (em maiúsculas) → região do IBGE; sem UF → `Não informada` | gold | teste: nenhuma venda com região nula |
| RN-07 | Eventos sem data ou de pedido órfão vão para a quarentena | silver | teste: quarentena contada e reportada |
| RN-08 | Usuário de vendas só vê a própria região (consultando a tabela de acesso) | governança (filtro de linha) | teste por perfil (aula 5) |
| RN-09 | E-mail e telefone mascarados fora do financeiro | governança (máscara) | teste por perfil (aula 5) |

## 5. Saída esperada

`gold.vendas_por_regiao`: uma linha por região e mês. Colunas: `regiao`, `mes`, `qtd_pedidos`, `valor_vendas` (R$), `ticket_medio`.
`gold.pedidos_concluidos`: um pedido por linha, para detalhamento, com os dados do cliente protegidos.

## 6. Fora do escopo desta versão

Devoluções, frete, impostos e atualização incremental (fica para o Módulo 02).

## Números de referência (semente 42, para conferir o lab)

| Métrica | Valor |
|---|---|
| Linhas com `status = 'entregue'` exato (Pessoa A) | 946 |
| Linhas “entregue” ignorando maiúsculas, com duplicadas (Pessoa B) | 1.060 |
| Pedidos com status atual entregue, seguindo RN-01 a RN-03 e RN-07 (Pessoa C) | **1.052** |
| Eventos duplicados / sem data / órfãos | 174 / 12 / 5 |
| Pedidos entregues de clientes sem UF | 4 |
