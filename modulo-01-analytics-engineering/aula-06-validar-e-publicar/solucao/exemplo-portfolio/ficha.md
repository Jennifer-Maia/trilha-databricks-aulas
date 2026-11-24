# Ficha do projeto

> Gerada por `scripts/gerar_ficha.py` a partir das tabelas, no perfil financeiro. Não digite estes números à mão.

| | |
|---|---|
| Fonte | API do Hugging Face (datasets-server), paginada, com retry e manifesto |
| Clientes · produtos · pedidos · eventos | 500 · 60 · 1500 · 5416 |
| O mesmo chamado, três contas | 946 (status exato) · 1060 (sem tratar duplicados) · **1052** (contrato) |
| Pedidos concluídos (ago–out/2026) | 1052 |
| Valor de vendas | R$ 2.302.177,12 |
| Região que mais vendeu | Sudeste (52% do valor) |
| Regras de negócio | 9 (RN-01 a RN-09), cada uma com teste |
| Testes de qualidade na última rodada | 9 de 9 OK |
| Governança | filtro por região (RN-08) e máscara de e-mail e telefone (RN-09) |
| Consumo | painel publicado sem credencial embutida + agente (Genie) com as regras do contrato |

## Vendas por região

| Região | Pedidos | Valor |
|---|---:|---:|
| Sudeste | 528 | R$ 1.201.242,08 |
| Nordeste | 187 | R$ 372.291,30 |
| Sul | 158 | R$ 354.946,71 |
| Norte | 89 | R$ 202.398,72 |
| Centro-Oeste | 86 | R$ 158.721,48 |
| Não informada | 4 | R$ 12.576,83 |
