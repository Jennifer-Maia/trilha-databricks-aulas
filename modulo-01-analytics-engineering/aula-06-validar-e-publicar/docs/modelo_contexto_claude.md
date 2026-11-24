# Contexto do projeto · Chamado #482 (para o Claude)

> Gerado pelo comando `/aula06-01-contexto`. É o "manual" que o Claude lê antes de mexer no seu projeto.
> Ele junta três coisas: **o contexto** (o que é o projeto), **as regras** (o contrato de dados) e **os parâmetros** (onde estão as tabelas).

## O projeto

Uma loja online **fictícia**. A Marina, gerente comercial, abriu o chamado #482: vendas por região, só pedidos concluídos, sem duplicidade, porque o último relatório não bateu com o financeiro. Cada time de vendas só vê a própria região, e só o financeiro vê e-mail e telefone.

Caminho dos dados: API do Hugging Face → landing (JSON cru) → bronze → silver → gold → testes → governança → painel e agente.

## Parâmetros

| | |
|---|---|
| Perfil da Databricks CLI | `{{perfil_cli}}` |
| Catálogo | `{{catalogo}}` |
| SQL warehouse | `{{warehouse_id}}` |
| Tabelas que o painel e o agente podem ler | `{{catalogo}}.gold.vendas_por_regiao`, `{{catalogo}}.gold.pedidos_concluidos` |
| Número de referência | **1.052** pedidos concluídos · **R$ 2.302.177,12** (perfil financeiro) |

Os ids do painel e do agente ficam em `meu-portfolio/parametros.json` (os scripts gravam sozinhos).

## Regras do contrato de dados (não mudar)

| ID | Regra |
|---|---|
| RN-01 | Status normalizado (`Entregue`, `ENTREGUE`, `delivered` → `entregue`) |
| RN-02 | Evento duplicado (mesmo `event_id`) conta uma vez |
| RN-03 | Status atual = evento mais recente do pedido |
| RN-04 | Pedido concluído = status atual `entregue` |
| RN-05 | Valor da venda = `valor_liquido` (com desconto) |
| RN-06 | Região = UF do cliente → região do IBGE; sem UF → `Não informada` |
| RN-07 | Evento sem data ou de pedido órfão vai para a quarentena |
| RN-08 | Vendas só vê a própria região (filtro de linha) |
| RN-09 | E-mail e telefone mascarados fora do financeiro |

Fora do escopo: devoluções, frete, impostos, produto/categoria, carga incremental.

## O que o Claude pode e não pode fazer

- **Pode:** rodar os scripts de `modulo-01-analytics-engineering/aula-06-validar-e-publicar/scripts/`, ler as tabelas gold e escrever arquivos em `meu-portfolio/`.
- **Não pode:** criar, apagar ou alterar tabelas (`DROP`, `DELETE`, `ALTER`, `CREATE OR REPLACE`), mudar o contrato, tirar o filtro ou a máscara, nem publicar o painel com credencial embutida.
- **Números:** todo número que for para o README ou para o post sai de `meu-portfolio/ficha.md`. Nunca digite um número de cabeça.
- **Perfil:** antes de gerar números, o perfil na tabela de acesso precisa ser `financeiro`. Em outro perfil o número sai filtrado, sem erro nenhum (o "528").
- **Dados:** são fictícios. Diga isso no README e no post. Nada de dado real, nome de empresa real ou e-mail de cliente.
- **Dúvida sobre recurso do Databricks:** cite a documentação oficial ou diga que não tem certeza.

## Como responder

Português do Brasil, frases curtas. Depois de cada comando, diga em 3 linhas: o que foi criado, onde abrir e qual regra do contrato isso protege.
