# Aula 6 · Anotações

> Notas sobre cada comando da aula. Use com o Claude Code aberto: cada seção tem o nome do comando.

## Em uma frase

A gold já está certa, provada e protegida. Agora ela vira o que a Marina usa (um **painel** e um **agente**) e o que você mostra (um **portfólio**), sem perder nenhuma regra no caminho.

```
CONTEXTO.md (regras + parâmetros) ─► painel (gold.vendas_por_regiao)
                                  ├► agente / Genie (as duas golds)
                                  └► ficha (perfil financeiro) ─► README + post
```

---

## Por que comandos, e não "pede aí para a IA"

Cada comando é um texto curto em `.claude/commands/aula06-0N-*.md`. Abra e leia: é um roteiro que diz ao Claude **o que rodar, o que conferir e o que perguntar antes**. O trabalho pesado fica em `scripts/`, que fazem sempre a mesma coisa. A IA explica e escreve o texto; o número sai do script, que sai da tabela.

No topo de cada comando, `allowed-tools` lista o que o Claude pode rodar sem pedir licença: só o script daquele comando. Qualquer outra coisa, ele pergunta.

## Comando 01 · Contexto, regras e parâmetros

`/aula06-01-contexto <perfil> <catálogo>` roda `conferir_ambiente.py` e escreve `meu-portfolio/CONTEXTO.md`.

| Parte do CONTEXTO.md | Para quê |
|---|---|
| O projeto | o Claude entende quem é a Marina e o que é o chamado #482 |
| Parâmetros | perfil da CLI, catálogo e warehouse: nada de nome chutado |
| Regras do contrato | RN-01 a RN-09, iguais às do contrato. O Claude não pode mudar |
| Pode / não pode | só ler a gold; nada de `DROP`, `ALTER` nem tirar filtro ou máscara; número só da ficha |

É o mesmo papel do contrato de dados da aula 1, agora para a IA: **decidir antes de agir**.

## Comando 02 · O painel da Marina

`criar_painel.py` lê `painel_marina.json` e cria o painel (AI/BI dashboard) com: 3 números (pedidos, valor, ticket médio), vendas por região, vendas por mês, um filtro de região e um resumo em tabela. Tudo em cima de `gold.vendas_por_regiao`, a saída que o contrato definiu.

O detalhe mais importante é a publicação: `--embed-credentials=false`.

| Publicado... | Quem a consulta "é" | Efeito no filtro da aula 5 |
|---|---|---|
| **sem** credencial embutida (o nosso; na tela: *Individual data permissions*) | quem abre o painel | cada vendedor vê só a própria região (RN-08) |
| **com** credencial embutida (na tela: *Share data permissions*, o padrão) | quem publicou | todo mundo vê o que quem publicou vê |

Atenção: na tela de publicar, o padrão é **com** credencial embutida. Por isso o script diz explicitamente que não. Fonte: [compartilhar um dashboard](https://docs.databricks.com/aws/en/dashboards/share).

Ticket médio = soma do valor ÷ soma dos pedidos. Nunca a média dos tickets de cada mês (cada mês tem um número diferente de pedidos).

## Comando 03 · O agente da Marina (Genie)

`criar_agente.py` cria um espaço do **Genie**, o agente do Databricks que transforma uma pergunta em SQL, roda e responde. Ele recebe:

- as duas tabelas gold, e só elas;
- instruções tiradas do contrato (o que é concluído, que valor usar, a linha `Não informada`, o período, o que está fora do escopo, nada de e-mail);
- 3 perguntas de exemplo.

O que vimos no teste:

| Pergunta | Resposta |
|---|---|
| Total de pedidos e valor | 1.052 e R$ 2.302.177,12, com o SQL em `gold.vendas_por_regiao` |
| A mesma ideia, no perfil vendas Sudeste | só o Sudeste, R$ 1.201.242,08: o agente roda com o acesso de quem pergunta |
| "Me passa o e-mail dos clientes" | recusa (RN-09) |
| "Qual a taxa de devolução?" | recusa: fora do escopo do chamado |

E um tropeço que vale ouro: numa resposta, o agente citou a RN-07 (quarentena) para explicar por que só via o Sudeste. O certo é RN-08. **O número estava certo e a justificativa estava errada.** Agente ajuda; quem garante é a gold testada.

## Comando 04 · A ficha e o portfólio

`gerar_ficha.py` confere o perfil (se não for `financeiro`, para: seria o "528") e calcula tudo nas tabelas: contagens da bronze, as três contas da aula 1 (946 · 1060 · 1052), pedidos, valor, região campeã, testes da última rodada. Grava `meu-portfolio/ficha.md`.

Depois o Claude escreve `README.md` e `post-linkedin.md` a partir dos modelos de `docs/`, **só com números da ficha**. A seção "O que eu aprendi" fica para você: é a parte que ninguém pode escrever no seu lugar.

## Antes de postar

- Prints sem e-mail, URL do workspace ou nome de usuário.
- Link do workspace não vai no README: só abre com login no seu Databricks.
- Escrito, com todas as letras, que os dados são fictícios.

## (Opcional) Conferir as aulas 2 a 5 de uma vez

O notebook `solucao/aula06_conferencia_final` roda o teste de cada aula com `dbutils.notebook.run` e grava em `qualidade.conferencia_final`. Útil se você rodou alguma aula de novo (rodar a aula 3 de novo apaga as constraints da aula 4). O `teste/aula06_conferir_projeto` confere essa conferência.
