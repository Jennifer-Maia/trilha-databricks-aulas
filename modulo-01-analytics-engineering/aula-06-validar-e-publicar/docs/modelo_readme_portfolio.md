# Modelo · README do seu projeto

> O comando `/aula06-04-portfolio` preenche este modelo em `meu-portfolio/README.md`. Depois, **revise com as suas palavras** e troque o que estiver entre `< >`.
> Regra de ouro: **todo número aqui saiu de uma tabela**. Use `meu-portfolio/ficha.md` (gerada no perfil `financeiro`).
> Apague estas três linhas de instrução antes de publicar.

---

# Vendas por região: do pedido vago ao número protegido

Projeto de Analytics Engineering no Databricks (Free Edition), sobre uma loja online **fictícia**. Um pedido vago do comercial ("quero as vendas por região") virou um contrato de dados, um pipeline com regra rastreável, testes que provam cada regra, acesso controlado na própria tabela e, no fim, **um painel e um agente de IA** para a gerente consultar sozinha.

![O projeto de ponta a ponta](img/aula-06-projeto-ponta-a-ponta.svg)

## O problema

O chamado #482 pediu as vendas concluídas por região, de agosto a outubro de 2026. Três pessoas com o mesmo pedido chegaram a três números diferentes (946, 1.060 e 1.052). A diferença entre elas era o que ninguém tinha decidido: o que é "concluído", o que é "duplicado", qual status vale.

## O que eu fiz

| Etapa | O que faz | Por quê |
|---|---|---|
| Contrato de dados | 9 regras numeradas (RN-01 a RN-09) | decidir antes de codar |
| Ingestão de API | paginação, retry com espera, validação de colunas, JSON cru + manifesto | a fonte manda; e "status 200" não prova que veio tudo |
| Bronze → silver → gold | cada regra com o número dela no código | qualquer número tem caminho de volta até a regra |
| Testes | contam linhas ruins, guardam histórico, constraints barram na entrada | um número só vale se existe um teste que pode falhar |
| Governança | filtro de linha por região e máscara de e-mail e telefone | a regra mora na tabela, não num documento |
| Painel (AI/BI dashboard) | pedidos, valor, ticket médio, vendas por região e por mês | publicado sem credencial embutida: cada pessoa vê só o que o perfil dela permite |
| Agente (Genie) | responde perguntas em português com as regras do contrato | recusa o que está fora do escopo e não mostra e-mail nem telefone |
| Contexto para IA | um arquivo com contexto, regras e parâmetros que o Claude Code lê antes de agir | a IA trabalha com o contrato, não com chute |

## Os números

<a tabela de meu-portfolio/ficha.md>

## O que a gerente recebe

<!-- print do painel: prints/painel.png -->

<!-- print de uma conversa com o agente: prints/agente.png -->

## O que eu aprendi

- <uma frase sua sobre o erro que mais te ensinou>
- <uma frase sua sobre teste × constraint, ou sobre a view que não protege>
- <uma frase sua sobre o que faria diferente com dado de verdade>

## Como rodar

1. Crie uma conta na Databricks Free Edition.
2. Clone este repositório como Git folder.
3. Rode, nesta ordem: `setup/01_criar_ambiente`, a ingestão, a transformação, os testes e a governança. Todos com o mesmo catálogo no widget.
4. Com a Databricks CLI e o Claude Code instalados, rode os comandos `/aula06-01-contexto` a `/aula06-04-portfolio` para criar o painel, o agente e esta ficha.

## Créditos

Projeto feito na Trilha Databricks da Jornada de Dados. Dados fictícios, gerados para estudo.
