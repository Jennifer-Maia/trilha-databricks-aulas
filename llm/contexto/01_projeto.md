# Contexto 01 · O projeto

## O que é

Material dos novos módulos de Databricks da **Jornada de Dados**. Cada módulo é um laboratório prático que roda na Databricks Free Edition (custo R$ 0) e evolui o mesmo projeto de portfólio. Cada módulo também funciona sozinho.

Fio condutor: **construir corretamente → entregar com segurança → operar e evoluir**.

## O cenário

Uma loja online fictícia. A gerente comercial abre o chamado #482:

> Preciso ver as vendas por região, considerando só pedidos concluídos e sem duplicidade, porque o número do último relatório não bateu com o financeiro. O time de vendas de cada região só pode ver a própria região. E ninguém fora do financeiro pode ver e-mail e telefone de cliente.

O pedido vira um **contrato de dados** (`modulo-01-analytics-engineering/docs/contrato_de_dados.md`), com perguntas, premissas e regras numeradas (RN-01 a RN-09). Cada regra vira código (aula 3) e teste (aula 4).

## Módulos

| Módulo | Tema | Certificação que apoia |
|---|---|---|
| 01 · Analytics Engineering com Databricks | Do pedido do negócio a uma tabela confiável: contrato, ingestão via API, medalhão, testes e governança por perfil | Data Analyst Associate |
| 02 · Por que minha tabela ficou lenta e cara? | Delta Lake por dentro, performance, carga incremental, custo e monitoramento | Data Engineer Associate |

### Aulas do Módulo 01

| # | Aula | Resultado |
|---|---|---|
| 1 | O pedido virou regra | Contrato de dados (sem código) |
| 2 | Ingerindo uma API de verdade | JSON bruto das 4 tabelas no Volume `raw.landing`, com manifesto |
| 3 | Transformação com regra rastreável | bronze → silver → gold (em breve) |
| 4 | Testes que provam a regra | testes salvos no schema `qualidade` (em breve) |
| 5 | Governança que protege de verdade | grants, filtro de linha, máscara (em breve) |
| 6 | Validar o consumo e publicar | teste por perfil e portfólio (em breve) |

## Arquitetura (Módulo 01)

```
API Hugging Face ──Python──▶ Volume raw.landing (JSON cru, uma pasta por carga + _manifesto.json)
      ──▶ bronze (fiel à origem + metadados) ──▶ silver (regras RN-01..03, RN-07; quarentena)
      ──▶ gold (vendas_por_regiao, pedidos_concluidos) ──▶ testes ──▶ governança ──▶ consumo por perfil
```

Catálogo padrão: `jornada_comercial`. Schemas: `raw`, `bronze`, `silver`, `gold`, `governanca`, `qualidade`.

## Organização das pastas

```
modulo-NN-slug/
├── docs/        contrato e documentos de apoio
├── setup/       prepara o ambiente do módulo + plano B sem API
└── aula-NN-slug/
    ├── README.md   passo a passo, checkpoint, tarefa
    ├── exercicio/  prática do aluno: exercícios curtos, cada um com uma célula "Conferir" (✅/❌)
    ├── solucao/    notebook da aula + gabarito dos exercícios
    ├── teste/      prova que o resultado está certo
    └── quiz.md     perguntas de múltipla escolha; a resposta fica escondida em <details>
```

Notebooks são arquivos `.py` no formato Databricks (começam com `# Databricks notebook source`; células separadas por `# COMMAND ----------`; markdown em linhas `# MAGIC`).
